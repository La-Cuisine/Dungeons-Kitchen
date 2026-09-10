import os
import shutil
from pathlib import Path
from PySide6.QtCore import QSettings, QTimer, Qt, QSize, QEventLoop
from PySide6.QtGui import QColor, QPalette, QPainter, QBrush, QPixmap, QIcon
from PySide6.QtWidgets import QGraphicsScene, QFileDialog, QPushButton, QScrollArea, QWidget, QVBoxLayout, QSizePolicy, QListWidgetItem, QInputDialog, QMessageBox,QDialog
from Custom_Widgets import *
from Custom_Widgets.QAppSettings import QAppSettings
from Custom_Widgets.QCustomTheme import QCustomTheme
import webbrowser
import xml.etree.ElementTree as ET

#------------Import interne------------#
from src.MJ_application.server import SERVER_URL, ServerController
from src.MJ_application.LogReaderThread import LogReaderThread
from src.MJ_application.grid import View_Grid, Grid, InvisibleWallLimit, DraggableImageList
from src.MJ_gamemode.MJ_gamemode import MainWindow as GameModeWindow
from src.MJ_application.img_divider import Divider_Window 
from src.MJ_application.Sym_const import *
from obj.blueprint import *
from obj.game import *
from obj.items import *
from obj.pawns import *
from obj.player import *
from obj.save import *
from obj.skills import *



class GuiFunctions():
    def __init__(self,MainWindow):
        self.main = MainWindow
        self.ui = MainWindow.ui
        self.init_var()
        self._controller = ServerController()
        self.settings =  QSettings("Dungeon Kitchen Company","Dungeon Kitchen")


        self.init_app_theme()
        self.init_action_menubar()
        self.init_app_btn_connect()
        self.init_info_menu()
        self.init_grid()
        self._init_inventory_scroll_areas()
        self._init_map_image_list()
        self._init_character_icon_row()

    # ----------------------------------------------------------------
    # Initialisation de l'application 
    # ----------------------------------------------------------------
    
    def init_var(self):
        """
        Initialisation des variables qui ont besoin
        d'être None ou vide à l'ouverture de l'application
        """
        self._log_thread = None
        self._game_window = None

        # Inventaire
        self._inventory_items = []  
        self._selected_inventory_row = None  
        self._editing_item_index = None 

        # Skill 
        self._character_skills = []  
        self._selected_skill_row = None  
        self._editing_skill_index = None  

        # Chemin relatifs vers des objets
        self._item_image_path = None  
        self._skill_image_path = None  
        self._character_icon_path = None  
        self._current_session_path = None 

    def init_app_theme(self):
        """
        Initialise le thème de l'application
        """
        self.themeEngine = QCustomTheme()
        current_theme = self.settings.value("THEME")
        # Ajoute des thèmes à la liste des thèmes
        self.ui.theme_list.addItem("Dark")
        self.ui.theme_list.addItem("Light")
        self.ui.theme_list.setCurrentText(current_theme)

        if current_theme == "Light":
            self._apply_light_theme()
        else:
            self._apply_dark_theme()

        # Couleur du label du menu "server"
        self.ui.server_state_label.setStyleSheet("color: #e74c3c; font-size: 13px;")

        # Cache des éléments à l'initialisation
        self.ui.alignement_NPC.setVisible(False)

        # Couleurs des boutons du menu "server"
        self.ui.open_server_btn.setStyleSheet(
            self._btn_style("#2ecc71", "#27ae60")
        )
        self.ui.close_server_btn.setStyleSheet(
            self._btn_style("#e74c3c", "#c0392b")
        )
        self.ui.open_website_btn.setStyleSheet(
            self._btn_style("#3498db", "#2980b9")
        )
        self.ui.open_game_interface_btn.setStyleSheet(
            self._btn_style("#db8534", "#be732c")
        )

        # Affiche le lien de l'URL correctement
        link = "URL : <a href='",SERVER_URL,"'>",SERVER_URL,"</a>"
        link_string = ''.join(link)
        self.ui.url_link_label.setText(link_string)

    def init_app_btn_connect(self):
        """
        Initialise les signaux pour les boutons de l'application
        """
        # Change le menu d'information
        self.ui.character_btn.clicked.connect(self.switch_to_character_menu)
        self.ui.map_btn.clicked.connect(self.switch_to_map_menu)
        self.ui.server_btn.clicked.connect(self.switch_to_server_menu)
        self.ui.settings_btn.clicked.connect(self.switch_to_settings_menu)
        self.ui.information_btn.clicked.connect(self.switch_to_information_menu)
        self.ui.help_btn.clicked.connect(self.switch_to_help_menu)
        self.ui.item_btn.clicked.connect(self.switch_to_item_menu)
        self.ui.skill_btn.clicked.connect(self.switch_to_skill_menu)

        # Ouvre ou ferme le menu d'information
        self.ui.open_info_menu_btn.clicked.connect(self.switch_center_menu_display_state)
        self.ui.close_info_menu_btn.clicked.connect(self.switch_center_menu_display_state)

        # Stat/Inv
        self.ui.isNPC.toggled.connect(self.setNPC)
        self.ui.add_item_btn.clicked.connect(self.add_item_to_character)
        self.ui.edit_item_btn.clicked.connect(self.edit_selected_item)
        self.ui.remove_item_btn.clicked.connect(self.remove_selected_item_from_character)
        self.ui.add_skill_btn.clicked.connect(self.add_skill_to_character)
        self.ui.edit_skill_btn.clicked.connect(self.edit_selected_skill)
        self.ui.remove_skill_btn.clicked.connect(self.remove_selected_skill_from_character)

        # Ouvre ou ferme le log/chat
        self.ui.close_log_view_btn.clicked.connect(self.switch_log_display_state)
        
        # Add images
        # Add images
        self.ui.add_cells_image_btn.clicked.connect(
            lambda: self.load_add_cells_img_btns()
        )
        # self.load_image(CELL_DIRECTORIES, self.ui.cells_image_list)

        self.ui.add_props_image_btn.clicked.connect(
            lambda: self.load_image(PROP_DIRECTORIES, self.ui.props_image_list)
        ) 

        self.ui.choose_item_img.clicked.connect(self.choose_item_image)
        self.ui.choose_skill_img.clicked.connect(self.choose_skill_image)
        # Note: choose_character_icon_btn is connected in _init_character_icon_row()

        # Save/Load
        self.ui.create_new_character_btn.clicked.connect(self.create_new_character)
        self.ui.save_character_btn.clicked.connect(self.save_character_stat)
        self.ui.load_character_btn.clicked.connect(self.load_character)
        self.ui.create_new_item_btn.clicked.connect(self.create_new_item)
        self.ui.save_item.clicked.connect(self.save_item)
        self.ui.load_item.clicked.connect(self.load_item)
        self.ui.create_new_skill_btn.clicked.connect(self.create_new_skill)
        self.ui.save_skill.clicked.connect(self.save_skill)
        self.ui.load_skill.clicked.connect(self.load_skill)
        self.ui.new_map_btn.clicked.connect(self.create_new_map)
        self.ui.save_map_btn.clicked.connect(self.save_map)
        self.ui.load_map_btn.clicked.connect(self.load_map)
        
        # Démarre ou ferme le serveur
        self.ui.open_server_btn.clicked.connect(self._update_server_label_open)
        self.ui.close_server_btn.clicked.connect(self._update_server_label_close)

        self.ui.open_server_btn.clicked.connect(self._start_server)
        self.ui.close_server_btn.clicked.connect(self._stop_server)
        self.ui.open_website_btn.clicked.connect(self._open_browser)
        self.ui.open_game_interface_btn.clicked.connect(self._open_game_interface)

        # Settings
        self.ui.theme_list.currentTextChanged.connect(self.changeAppTheme)
    
    def _init_inventory_scroll_areas(self):
        """
        Remplace les QGridLayout item_grid et skill_grid (définis dans le fichier
        UI auto-généré) par des QScrollArea contenant un QVBoxLayout dédié.
        Cela permet d'afficher un ascenseur vertical dès que la liste dépasse
        la hauteur disponible, sans modifier le fichier UI.
        """
        # --- Inventory (items) ---
        # Retire le QGridLayout nu de son parent et le remplace par un QScrollArea
        inventory_parent_layout = self.ui.verticalLayout_18  # layout du tab "inventory"

        # Supprime l'ancien item_grid du parent layout
        index = inventory_parent_layout.indexOf(self.ui.item_grid)
        inventory_parent_layout.removeItem(self.ui.item_grid)

        # Crée le conteneur interne (QWidget + QVBoxLayout) pour les boutons
        self._item_list_widget = QWidget()
        self._item_list_layout = QVBoxLayout(self._item_list_widget)
        self._item_list_layout.setContentsMargins(0, 0, 0, 0)
        self._item_list_layout.setSpacing(2)
        self._item_list_layout.addStretch()  # pousse les boutons vers le haut

        # Crée le QScrollArea
        self._item_scroll_area = QScrollArea()
        self._item_scroll_area.setWidgetResizable(True)
        self._item_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._item_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._item_scroll_area.setWidget(self._item_list_widget)
        self._item_scroll_area.setFrameShape(self._item_scroll_area.Shape.NoFrame)

        # Insère le QScrollArea exactement là où était item_grid
        inventory_parent_layout.insertWidget(index, self._item_scroll_area, 1)

        # --- skill list ---
        skill_parent_layout = self.ui.verticalLayout_16  # layout du tab "skill"

        index_skill = skill_parent_layout.indexOf(self.ui.skill_grid)
        skill_parent_layout.removeItem(self.ui.skill_grid)

        self._skill_list_widget = QWidget()
        self._skill_list_layout = QVBoxLayout(self._skill_list_widget)
        self._skill_list_layout.setContentsMargins(0, 0, 0, 0)
        self._skill_list_layout.setSpacing(2)
        self._skill_list_layout.addStretch()

        self._skill_scroll_area = QScrollArea()
        self._skill_scroll_area.setWidgetResizable(True)
        self._skill_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._skill_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._skill_scroll_area.setWidget(self._skill_list_widget)
        self._skill_scroll_area.setFrameShape(self._skill_scroll_area.Shape.NoFrame)

        skill_parent_layout.insertWidget(index_skill, self._skill_scroll_area, 1)

    def _init_character_icon_row(self):
        """
        Insère dynamiquement, au-dessus du champ character_name, une ligne
        composée de :
          - un QLabel carré (48×48) affichant l'icône du personnage
          - le champ character_name existant (déplacé dans ce layout)
          - un QPushButton « 🖼 » pour choisir l'icône

        Tout est injecté dans verticalLayout_12 sans toucher au fichier UI.
        """
        from PySide6.QtWidgets import QHBoxLayout, QLabel

        parent_layout = self.ui.verticalLayout_12  # layout du character_menu

        # --- Retire character_name de son emplacement actuel ---
        parent_layout.removeWidget(self.ui.character_name)

        # --- Label aperçu de l'icône (48×48) ---
        self._character_icon_label = QLabel()
        self._character_icon_label.setFixedSize(QSize(48, 48))
        self._character_icon_label.setScaledContents(True)
        self._character_icon_label.setPixmap(QPixmap(PLACEHOLDER_IMAGE))
        self._character_icon_label.setStyleSheet(
            "border: 1px solid #555; border-radius: 4px;"
        )

        # --- Bouton pour choisir l'icône ---
        self._choose_character_icon_btn = QPushButton("🖼")
        self._choose_character_icon_btn.setToolTip("Choisir une icône pour le personnage")
        self._choose_character_icon_btn.setFixedSize(QSize(30, 30))
        self._choose_character_icon_btn.clicked.connect(self.choose_character_icon)

        # --- Ligne horizontale : [icône] [character_name] [bouton] ---
        icon_row_widget = QWidget()
        icon_row_widget.setMaximumHeight(48)
        icon_row_layout = QHBoxLayout(icon_row_widget)
        icon_row_layout.setContentsMargins(0, 0, 0, 0)
        icon_row_layout.setSpacing(4)
        icon_row_layout.addWidget(self._character_icon_label)
        icon_row_layout.addWidget(self.ui.character_name)
        icon_row_layout.addWidget(self._choose_character_icon_btn)

        # --- Insère la ligne en position 0 (tout en haut du character_menu) ---
        parent_layout.insertWidget(0, icon_row_widget)

    def _populate_image_list(self, list_widget, directories):
        """
        Populate a QListWidget with images found in several folders.
        """
        list_widget.clear()

        images = {}

        for directory in directories:
            if not directory.is_dir():
                continue

            for file in directory.iterdir():
                if file.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue

                # local folder overrides base folder
                images[file.name] = file

        for file in sorted(images.values(), key=lambda p: p.name.lower()):
            item = QListWidgetItem(file.name)

            pixmap = QPixmap(str(file))
            if not pixmap.isNull():
                item.setIcon(
                    QIcon(
                        pixmap.scaled(
                            32,
                            32,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                )

            item.setData(Qt.ItemDataRole.UserRole, str(file))
            list_widget.addItem(item)

    def _init_map_image_list(self):
        """
        Remplace les QListWidget generes par Qt Designer (cells_image_list,
        props_image_list) par des DraggableImageList : meme apparence et
        meme comportement, mais leurs items peuvent desormais etre glisses
        (drag and drop) vers une case de la grille pour y deposer l'image.

        Remplit ensuite les panneaux Cells et Props.
        """

        if hasattr(self.ui, "cells_image_list") and hasattr(self.ui, "verticalLayout_cells"):
            self.ui.cells_image_list = self._make_draggable_image_list(
                self.ui.cells_image_list, self.ui.verticalLayout_cells, role="cell"
            )
            self._populate_image_list(
                self.ui.cells_image_list,
                CELL_DIRECTORIES
            )

        if hasattr(self.ui, "props_image_list") and hasattr(self.ui, "verticalLayout_props"):
            self.ui.props_image_list = self._make_draggable_image_list(
                self.ui.props_image_list, self.ui.verticalLayout_props, role="prop"
            )
            self._populate_image_list(
                self.ui.props_image_list,
                PROP_DIRECTORIES
            )

    def _make_draggable_image_list(self, old_list, layout, role: str = "cell"):
        """
        Remplace old_list (QListWidget cree par Qt Designer) par un
        DraggableImageList insere au meme endroit dans layout, en
        conservant son nom d'objet et la taille de ses icones.
        Renvoie la nouvelle instance (a reassigner sur self.ui.<nom>).
        """
        index = layout.indexOf(old_list)
        name = old_list.objectName()
        icon_size = old_list.iconSize()
        parent = old_list.parentWidget()

        layout.removeWidget(old_list)
        old_list.deleteLater()

        new_list = DraggableImageList(parent, role=role)
        new_list.setObjectName(name)
        new_list.setIconSize(icon_size)
        new_list.setUniformItemSizes(True)

        layout.insertWidget(index, new_list)
        return new_list

    def init_action_menubar(self):
        """
        Initialise les signaux pour les actions de la menubar
        """
        # Display menu
        self.ui.actionLog_Chat.toggled.connect(self.switch_log_display_state)
        self.ui.actionInfo_menu.toggled.connect(self.switch_center_menu_display_state)
        
        # Close application
        self.ui.actionClose.triggered.connect(self.closeEvent)

        # New object
        self.ui.actionNew_character.triggered.connect(self.create_new_character)
        self.ui.actionNew_item.triggered.connect(self.create_new_item)
        self.ui.actionNew_skill.triggered.connect(self.create_new_skill)
        self.ui.actionNew_map.triggered.connect(self.create_new_map)
        
        # Load object
        self.ui.actionOpen_character.triggered.connect(self.load_character)
        self.ui.actionOpen_item.triggered.connect(self.load_item)
        self.ui.actionOpen_skill.triggered.connect(self.load_skill)
        #self.ui.actionOpen_map.triggered.connect(self.load_map)
        
        # Save/Save as
        self.ui.actionSave.triggered.connect(self.save_actionmenu)
        #self.ui.actionSave_as.triggered.connect(self.save_as_actionmenu)

        # Save/Load session (sauvegarde le dossier local/ dans projects/,
        # et recharge un projet sauvegardé dans local/)
        self.ui.actionNew_session.triggered.connect(self.new_session)
        self.ui.actionSave_session.triggered.connect(self.save_session)
        self.ui.actionUpdate_session.triggered.connect(self.update_session)
        self.ui.actionLoad_session.triggered.connect(self.load_session)

    def init_info_menu(self):
        """
        Ouvre la dernière page consulté de information menu au 
        lancement de l'application. 
        Ouvre la page du serveur si il n'y pas d'information sur
        la dernière page consulté.
        """
        self.last_menu = self.settings.value("MENU INFO")

        if(isinstance(self.last_menu, int)):
            self.ui.stacked_widget.setCurrentIndex(self.last_menu)
        else:
            self.switch_to_server_menu()

    def init_grid(self, n: int = 50, s_cell: int = 64):
        """
        Remplace le QGraphicsView généré par Qt Designer par un View_Grid,
        puis y injecte la scène, le mur invisible et la grille.

        :param n:      Nombre de cellules par côté de la grille.
        :param s_cell: Taille en pixels d'une cellule.
        """
        import src.MJ_application.grid as _grid_module

        # Recupere le layout parent du graphicsView
        layout = self.ui.verticalLayout_10

        # Cree la scene graphique
        self._scene = QGraphicsScene()
        self._scene.setSceneRect(0, 0, 700, 520)
        # Desactive l'index BSP : inutile pour une grille rigide,
        # evite de recalculer les bounding rects de tous les enfants au drag.
        self._scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # Crée le View_Grid et le branche sur la scène
        self._view_grid = View_Grid(self._scene)
        self._view_grid.setObjectName("graphicsView")
        self._view_grid.setRenderHint(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self._view_grid.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_grid.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view_grid.setBackgroundBrush(QBrush(QColor("#171717ff")))
        self._view_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._view_grid.setDragMode(View_Grid.DragMode.ScrollHandDrag)
        self._view_grid.setMouseTracking(True)

        # Insere le View_Grid AVANT de creer l'overlay (la vue doit etre
        # dans le layout pour avoir une taille et un parent valides).
        layout.insertWidget(0, self._view_grid)

        # Overlay coordonnees souris : QLabel enfant de la vue (plus un item scene).
        # Taille fixe, toujours en haut a droite, insensible au pan/zoom.
        self.InterMouseCoor = _grid_module.Interface_MouseCoord(self._view_grid)
        self._view_grid.addItemNeeds(self.InterMouseCoor)

        # Mur invisible (doit exister avant la grille)
        self._wall = InvisibleWallLimit(self._scene)
        _grid_module._wall = self._wall          # Met à jour la globale du module
        self._scene.addItem(self._wall)

        # Grille
        self._build_grid(n, s_cell)

        # Met à jour la référence ui.graphicsView pour que le reste du code
        # continue à fonctionner via self.ui.graphicsView si besoin
        self.ui.graphicsView = self._view_grid

    # ------------------------------------------------------------------
    # Image de l'objet / du sort (choose_item_img, choose_skill_img)
    # ------------------------------------------------------------------

    def choose_item_image(self):
        """
        Slot connecté au signal clicked du bouton "choose_item_img".
        Ouvre un sélecteur de fichier, copie l'image choisie dans le
        dossier d'assets local des objets, met à jour l'aperçu (item_img)
        et mémorise le chemin pour qu'il soit sauvegardé avec l'objet
        dans save_item().
        """
        path = self._choose_and_store_image(ITEM_DIRECTORIES)
        if path is None:
            return

        self._item_image_path = path
        self.ui.item_img.setPixmap(QPixmap(path))

    def choose_skill_image(self):
        """
        Slot connecté au signal clicked du bouton "choose_skill_img".
        Équivalent de choose_item_image() pour le sort en cours d'édition.
        """
        path = self._choose_and_store_image(SKILL_DIRECTORIES)
        if path is None:
            return

        self._skill_image_path = path
        self.ui.skill_img.setPixmap(QPixmap(path))

    def choose_character_icon(self):
        """
        Slot connecté au bouton 🖼 dans la ligne au-dessus du nom du personnage.
        Ouvre un sélecteur de fichier image, copie l'image dans le dossier
        local des icônes de personnages, met à jour le label aperçu et
        mémorise le chemin dans _character_icon_path pour qu'il soit
        sauvegardé avec la fiche dans save_character_stat().
        """
        path = self._choose_and_store_image(CHARACTER_ICON_DIRECTORIES)
        if path is None:
            return

        self._character_icon_path = path
        self._character_icon_label.setPixmap(QPixmap(path))

    def _choose_and_store_image(self, directories):
        """
        Ouvre un sélecteur de fichier image, copie le fichier choisi dans
        le dossier local (directories[-1], créé si besoin, même logique
        que load_image()) et renvoie son chemin absolu.

        Renvoie None si l'utilisateur annule la sélection ou si la copie
        échoue (un message est alors ajouté au log).
        """
        filename, _ = QFileDialog.getOpenFileName(
            self.main,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp *.PNG)"
        )

        if not filename:
            return None

        source = Path(filename)
        local_dir = directories[-1]
        local_dir.mkdir(parents=True, exist_ok=True)
        destination = local_dir / source.name

        try:
            import shutil

            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)

            self._append_log(
                f"[INFO] Image '{source.name}' copiée dans '{local_dir}'."
            )
            return str(destination)
        except Exception as exc:
            self._append_log(
                f"[ERREUR] Impossible d'ajouter l'image : {exc}"
            )
            return None

    def _build_item(self, name, type_, description, image_path):
        """
        Construit un Item à partir des champs du formulaire et lui
        attribue l'image choisie via new_reference() (obj/items.py).
        """
        item = Item(Name=name, Type=type_, Description=description)
        if image_path:
            item.new_reference(image_path)
        return item

    def _build_skill(self, name, type, description, image_path):
        """
        Équivalent de _build_item() pour les sorts (Skill).
        """
        skill = Skill(Name=name, Type=type, Description=description)
        if image_path:
            skill.new_reference(image_path)
        return skill

    def _image_path_of(self, obj):
        """
        Récupère le chemin d'image stocké sur un Item/Skill déjà
        construit (via image_reference(), cf. obj/items.py et
        obj/skills.py). Renvoie None si l'objet n'a pas d'image.
        """
        path = obj.image_reference()
        return path or None

    def _build_grid(self, n: int, s_cell: int = 64):
        """
        Construit une grille (n x n cellules) et l'ajoute à la scène.

        Si une grille existait déjà sur la scène (self._world), elle est
        retirée au préalable : cette méthode peut donc aussi bien servir
        à l'initialisation de la grille qu'au remplacement par une
        nouvelle carte vide (voir create_new_map()).

        :param n:      Nombre de cellules par côté de la grille.
        :param s_cell: Taille en pixels d'une cellule.
        """
        from PySide6.QtWidgets import QGraphicsItem

        if getattr(self, "_world", None) is not None:
            self._scene.removeItem(self._world)

        self._world = Grid(n, s_cell)
        (self._world.atoms[0]).setName("TL")
        (self._world.atoms[0]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        (self._world.atoms[n - 1]).setName("TR")
        (self._world.atoms[n - 1]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        (self._world.atoms[(n - 1) * n]).setName("BL")
        (self._world.atoms[(n - 1) * n]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        (self._world.atoms[(n - 1) * n + (n - 1)]).setName("BR")
        (self._world.atoms[(n - 1) * n + (n - 1)]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._scene.addItem(self._world)

        # Reference directe sur la grille pour que _cell_at_view_pos()
        # fonctionne meme avant le premier mouseMoveEvent.
        self._view_grid._grid = self._world

    def create_new_map(self):
        """
        Crée une nouvelle carte vide : demande à l'utilisateur le nombre
        de cellules par côté, confirme (la carte affichée actuellement
        sera remplacée), puis reconstruit la grille avec _build_grid().
        """
        n, ok = QInputDialog.getInt(
            self.main,
            "Nouvelle carte",
            "Nombre de cellules par côté :",
            10,   # valeur par défaut
            1,    # minimum
            200,  # maximum
            1     # pas
        )
        if not ok:
            return

        confirm = QMessageBox.question(
            self.main,
            "Nouvelle carte",
            "La carte actuellement affichée sera remplacée par une carte "
            f"vide de {n}x{n} cellules. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._build_grid(n)
        self._append_log(f"[INFO] Nouvelle carte créée ({n}x{n} cellules)")

    # ----------------------------------------------------------------
    # Slots – méthodes connectées aux signaux des boutons et du thread
    # ----------------------------------------------------------------
    
    def _start_server(self):
        """
        Slot connecté au signal clicked du bouton "Démarrer le serveur".

        Séquence d'actions :
          1. Appelle ServerController.start() pour lancer le processus PHP.
          2. Instancie LogReaderThread avec le Popen retourné.
          3. Connecte le signal new_line du thread à _append_log (ce slot
             s'exécutera dans l'UI thread grâce au mécanisme Qt).
          4. Démarre le thread de lecture des logs.
          5. Met à jour les boutons et la barre d'état.
        """
        try:
            # Délègue le démarrage du processus PHP à ServerController (server.py)
            process = self._controller.start()
        except (FileNotFoundError, RuntimeError) as exc:
            # En cas d'erreur (PHP absent, serveur déjà lancé…), affiche le message
            # dans la zone de logs sans faire crasher l'application.
            self._append_log(f"[ERREUR] {exc}")
            return

        # Crée le thread qui lira les logs du processus PHP en temps réel
        self._log_thread = LogReaderThread(process)

        # Connecte le signal new_line → slot _append_log.
        # Qt s'assure que _append_log s'exécute dans l'UI thread (thread-safe).
        self._log_thread.new_line.connect(self._append_log)

        # Lance le thread secondaire (appelle run() dans un thread OS séparé)
        self._log_thread.start()

        # Met à jour la barre d'état avec un message vert (serveur actif)
        self._set_status(f"Serveur en cours d'exécution sur {SERVER_URL}", "#2ecc71")
        self._append_log(f"[INFO] Serveur PHP démarré → {SERVER_URL}")
        self._update_server_label_open()

    def _stop_server(self):
        """
        Slot connecté au signal clicked du bouton "Arrêter le serveur".

        Séquence d'actions :
          1. Arrête le thread de lecture des logs (stop() + wait()).
          2. Appelle ServerController.stop() pour tuer le processus PHP.
          3. Met à jour les boutons et la barre d'état.

        L'ordre est important : on arrête le thread AVANT le processus pour
        éviter que le thread tente de lire un stdout fermé.
        """

        if self._log_thread is None:
            self._append_log("[ERREUR] Serveur ne peut pas être arrêté (Serveur n'est pas ouvert).")

        else:
            # 1. Signale au thread de ne plus émettre de nouveaux logs
            self._log_thread.stop()   # Positionne le drapeau _running à False
    
            # 2. Arrête le processus PHP → provoque l'EOF sur stdout du thread
            self._controller.stop()
    
            # 3. Attend la fin du thread (désormais débloqué par l'EOF)
            self._log_thread.wait(3000)   # Timeout 3 s en sécurité (ne bloque plus)
            self._log_thread = None       # Libère la référence pour le garbage collector
    
            # Met à jour la barre d'état avec un message rouge (serveur arrêté)
            self._set_status("Serveur arrêté", "#e74c3c")
            self._append_log("[INFO] Serveur PHP arrêté.")
            self._update_server_label_close()

    def _open_browser(self):
        """
        Slot connecté au signal clicked du bouton "Ouvrir dans le navigateur".
        Délègue l'ouverture de l'URL au module webbrowser de Python,
        qui utilise le navigateur par défaut du système d'exploitation.
        """
        if self._log_thread is None:
            self._append_log("[ERREUR] Site ne peut pas s'ouvrir (Serveur n'est pas ouvert).")
        else:
            webbrowser.open(SERVER_URL)   # Ouvre http://127.0.0.1:8080 dans le navigateur
            self._append_log(f"[INFO] Navigateur ouvert sur {SERVER_URL}")

    # ----------------------------------------------------------------
    # Menu d'information 
    # ----------------------------------------------------------------

    def switch_to_settings_menu(self):
        """
        Ouvre le menu settings
        """
        self.ui.stacked_widget.setCurrentIndex(0)
        self.settings.setValue("MENU INFO",0)
        self._open_center_menu()

    def switch_to_character_menu(self):
        """
        Ouvre le menu character
        """
        self.ui.stacked_widget.setCurrentIndex(1)
        self.settings.setValue("MENU INFO",1)
        self._open_center_menu()    

    def switch_to_map_menu(self):
        """
        Ouvre le menu map
        """
        self.ui.stacked_widget.setCurrentIndex(2)
        self.settings.setValue("MENU INFO",2)
        self._open_center_menu()
    
    def switch_to_server_menu(self):
        """
        Ouvre le menu server
        """
        self.ui.stacked_widget.setCurrentIndex(3)
        self.settings.setValue("MENU INFO",3)
        self._open_center_menu()

    def switch_to_information_menu(self):
        """
        Ouvre le menu information
        """
        self.ui.stacked_widget.setCurrentIndex(4)
        self.settings.setValue("MENU INFO",4)
        self._open_center_menu()

    def switch_to_help_menu(self):
        """
        Ouvre le menu help
        """
        self.ui.stacked_widget.setCurrentIndex(5)
        self.settings.setValue("MENU INFO",5)
        self._open_center_menu()

    def switch_to_item_menu(self):
        """
        Ouvre le menu item
        """
        self.ui.stacked_widget.setCurrentIndex(6)
        self.settings.setValue("MENU INFO",6)
        self._open_center_menu()

    def switch_to_skill_menu(self):
        """
        Ouvre le menu skill
        """
        self.ui.stacked_widget.setCurrentIndex(7)
        self.settings.setValue("MENU INFO",7)
        self._open_center_menu()

    def _open_center_menu(self):
        """
        Affiche le menu d'information
        """
        # Déconnecte actionInfo_menu du signal
        self.ui.actionInfo_menu.blockSignals(True)
        
        self.ui.center_menu.setVisible(True)
        self.ui.open_info_menu_btn.setIcon(QIcon("ui/image/Undo.png"))
        self.ui.actionInfo_menu.setChecked(True)

        # Reconnecte actionInfo_menu du signal
        self.ui.actionInfo_menu.blockSignals(False)

    def _close_center_menu(self):
        """
        Cache le menu d'information
        """       
        # Déconnecte actionInfo_menu du signal
        self.ui.actionInfo_menu.blockSignals(True)

        self.ui.center_menu.setVisible(False)
        self.ui.open_info_menu_btn.setIcon(QIcon("ui/image/Redo.png"))
        self.ui.actionInfo_menu.setChecked(False)

        # Reconnecte actionInfo_menu du signal
        self.ui.actionInfo_menu.blockSignals(False)

    def switch_center_menu_display_state(self):
        """
        Affiche ou cache le menu d'information selon
        l'état de visibilité du menu
        """
        # Déconnecte actionInfo_menu du signal
        self.ui.actionInfo_menu.blockSignals(True)
        
        # Cacher la fenêtre
        if(self.ui.center_menu.isVisible() == True):
            self._close_center_menu()

        # Afficher la fenêtre
        elif(self.ui.center_menu.isVisible() == False):
            self._open_center_menu()
        
        else:
            print("Erreur switch center menu display")

        # Reconnecte actionInfo_menu du signal
        self.ui.actionInfo_menu.blockSignals(False)
            
    # ----------------------------------------------------------------
    # Stat/Inv/skill
    # ----------------------------------------------------------------

    def setNPC(self):
        """
        Affiche ou cache les options liées au NPC
        """
        # Active le choix de l'alignement d'un npc
        if(self.ui.isNPC.isChecked() == True):
            self.ui.alignement_NPC.setVisible(True)

        # Désactive le choix de l'alignement d'un npc
        elif(self.ui.isNPC.isChecked() == False):
            self.ui.alignement_NPC.setVisible(False)

        else:
            print("Erreur setNPC")

    #--------Création d'objet----------#

    def create_new_character(self):
        """
        Slot connecté au signal clicked du bouton "Create new character".
        Vide le panneau de personnage pour permettre la saisie d'une
        nouvelle fiche, et bascule sur le menu Character.
        """
        # Réinitilialise les widgets
        self.ui.character_name.setText(None)
        self.ui.hp_nb.setValue(0)
        self.ui.str_nb.setValue(0)
        self.ui.dex_nb.setValue(0)
        self.ui.con_nb.setValue(0)
        self.ui.int_nb.setValue(0)
        self.ui.wis_nb.setValue(0)
        self.ui.cha_nb.setValue(0)

        # Réinitialise l'icône du personnage
        self._character_icon_path = None
        self._character_icon_label.setPixmap(QPixmap(PLACEHOLDER_IMAGE))

        # Décoche la case isNPC
        self.ui.isNPC.blockSignals(True)
        self.ui.isNPC.setChecked(False)
        self.ui.isNPC.blockSignals(False)

        # setNPC() n'est pas déclenché automatiquement (signal bloqué
        # ci-dessus), donc on cache/réinitialise l'alignement à la main.
        self.ui.alignement_NPC.setCurrentIndex(0)
        self.setNPC()

        # Réinitilialise l'inventaire
        self._inventory_items = []
        self._selected_inventory_row = None
        self._refresh_inventory_grid()

        # Réinitilialise la liste de sorts
        self._character_skills = []
        self._selected_skill_row = None
        self._refresh_skill_grid()

        # Affiche le panneau Character pour la saisie
        self.switch_to_character_menu()

    def create_new_item(self):
        """
        Slot connecté au signal clicked du bouton \"Create new item\".
        Vide le panneau Item pour permettre la saisie d'un
        nouvel objet, et bascule sur le menu Item.
        """
        # Mode création : aucun objet existant n'est en cours d'édition
        self._editing_item_index = None

        # Réinitialise les champs de l'objet
        self.ui.item_name.setText("")
        self.ui.item_type.setCurrentIndex(0)
        self.ui.item_description.clear()
        self._item_image_path = None
        self.ui.item_img.setPixmap(QPixmap(PLACEHOLDER_IMAGE))

        # Affiche le panneau Item pour la saisie
        self.switch_to_item_menu()

    def create_new_skill(self):
        """
        Slot connecté au signal clicked du bouton \"Create new skill\".
        Vide le panneau skill pour permettre la saisie d'un
        nouveau sort, et bascule sur le menu skill.
        """
        # Mode création : aucun sort existant n'est en cours d'édition
        self._editing_skill_index = None

        # Réinitialise les champs du sort
        self.ui.skill_name.setText("")
        self.ui.skill_description.clear()
        self._skill_image_path = None
        self.ui.skill_img.setPixmap(QPixmap(PLACEHOLDER_IMAGE))

        # Affiche le panneau skill pour la saisie
        self.switch_to_skill_menu()

    #---------Ajout d'objet----------#

    def add_item_to_character(self):
        """
        Slot connecté au signal clicked du bouton "Add item".
        Ouvre un sélecteur de fichier pour choisir un objet (.xml,
        normalement sous ./local/Items/...) et l'ajoute à l'inventaire
        du personnage en cours de création/édition.
        """
        try:
            item = self.load_xml()
        except Exception as exc:
            # L'utilisateur a annulé la sélection, ou le fichier est invalide
            self._append_log(f"[ERREUR] {exc}")
            return

        if not isinstance(item, Item):
            self._append_log("[ERREUR] Le fichier sélectionné n'est pas un objet (Item) valide.")
            return

        # Ajoute l'objet à l'inventaire en mémoire et rafraîchit l'affichage
        self._inventory_items.append(item)
        self._refresh_inventory_grid()

    def add_skill_to_character(self):
        """
        Slot connecté au signal clicked du bouton "Add skill" (panneau skill
        de la fiche de personnage). Ouvre un sélecteur de fichier pour
        choisir un sort (.xml, normalement sous ./local/skills/) et l'ajoute
        à la liste de sorts du personnage en cours de création/édition.
        """
        try:
            skill = self.load_xml()
        except Exception as exc:
            # L'utilisateur a annulé la sélection, ou le fichier est invalide
            self._append_log(f"[ERREUR] {exc}")
            return

        if not isinstance(skill, Skill):
            self._append_log("[ERREUR] Le fichier sélectionné n'est pas un sort (Skill) valide.")
            return

        # Ajoute le sort à la liste en mémoire et rafraîchit l'affichage
        self._character_skills.append(skill)
        self._refresh_skill_grid()

    #---------Retire d'objet----------#

    def remove_selected_item_from_character(self):
        """
        Slot connecté au signal clicked du bouton "Remove item".
        Retire de l'inventaire en cours d'édition l'objet actuellement
        sélectionné dans la liste (aucune action si rien n'est sélectionné).
        """
        if self._selected_inventory_row is None:
            self._append_log("[ERREUR] Aucun objet sélectionné dans l'inventaire.")
            return

        del self._inventory_items[self._selected_inventory_row]
        self._selected_inventory_row = None
        self._refresh_inventory_grid()

    def remove_selected_skill_from_character(self):
        """
        Slot connecté au signal clicked du bouton "Remove skill".
        Retire de la liste de sorts en cours d'édition le sort actuellement
        sélectionné (aucune action si rien n'est sélectionné).
        """
        if self._selected_skill_row is None:
            self._append_log("[ERREUR] Aucun sort sélectionné dans la liste.")
            return

        del self._character_skills[self._selected_skill_row]
        self._selected_skill_row = None
        self._refresh_skill_grid()

    #---------Edition d'objet----------#

    def edit_selected_item(self):
        """
        Slot connecté au signal clicked du bouton "Edit item".
        Pré-remplit le formulaire Item avec les données de l'objet
        sélectionné dans l'inventaire et bascule vers le menu Item.
        L'index de l'objet est mémorisé dans _editing_item_index pour que
        save_item() mette à jour l'entrée existante au lieu d'en créer une.
        """
        if self._selected_inventory_row is None:
            self._append_log("[ERREUR] Aucun objet sélectionné dans l'inventaire.")
            return

        item = self._inventory_items[self._selected_inventory_row]
        self._editing_item_index = self._selected_inventory_row

        # Pré-remplit le formulaire avec les données de l'objet
        self.ui.item_name.setText(item.name())
        self.ui.item_type.setCurrentText(item.type())
        self.ui.item_description.setText(item.description())
        self._item_image_path = self._image_path_of(item)
        self.ui.item_img.setPixmap(QPixmap(self._item_image_path or PLACEHOLDER_IMAGE))

        # Bascule vers le menu Item
        self.switch_to_item_menu()

    def edit_selected_skill(self):
        """
        Slot connecté au signal clicked du bouton "Edit skill".
        Pré-remplit le formulaire skill avec les données du sort sélectionné
        dans la liste et bascule vers le menu skill.
        L'index du sort est mémorisé dans _editing_skill_index pour que
        save_skill() mette à jour l'entrée existante au lieu d'en créer une.
        """
        if self._selected_skill_row is None:
            self._append_log("[ERREUR] Aucun sort sélectionné dans la liste.")
            return

        skill = self._character_skills[self._selected_skill_row]
        self._editing_skill_index = self._selected_skill_row

        # Pré-remplit le formulaire avec les données du sort
        self.ui.skill_name.setText(skill.name())
        self.ui.skill_description.setText(skill.description())
        self._skill_image_path = self._image_path_of(skill)
        self.ui.skill_img.setPixmap(QPixmap(self._skill_image_path or PLACEHOLDER_IMAGE))

        # Bascule vers le menu skill
        self.switch_to_skill_menu()

    #---------Sélection d'objet----------#

    def _select_inventory_row(self, row):
        """
        Mémorise la ligne actuellement sélectionnée dans la liste de
        l'inventaire et affiche sa description (appelé quand l'utilisateur
        clique sur un objet).
        """
        self._selected_inventory_row = row
        self.ui.item_desc_display.setPlainText(self._inventory_items[row].description())

    def _select_skill_row(self, row):
        """
        Mémorise la ligne actuellement sélectionnée dans la liste de
        sorts et affiche sa description (appelé quand l'utilisateur
        clique sur un sort).
        """
        self._selected_skill_row = row
        self.ui.skill_desc_display.setPlainText(self._character_skills[row].description())

    #---------Rafraichisement des objets----------#

    def _refresh_inventory_grid(self):
        """
        Reconstruit entièrement l'affichage de la liste d'objets dans la
        QScrollArea de l'inventaire : une liste verticale (du haut vers le bas,
        une seule colonne) d'objets sélectionnables.
        Le bouton "Remove item" retire l'objet sélectionné.
        """
        layout = self._item_list_layout

        # Vide le layout (en conservant le stretch final)
        while layout.count() > 1:  # garde le stretch en dernière position
            child = layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        # Vide la description tant qu'aucune sélection n'est restaurée
        self.ui.item_desc_display.clear()

        # Reconstruit une ligne par objet, du haut vers le bas
        for row, item in enumerate(self._inventory_items):
            btn = QPushButton(f"{item.name()} ({item.type()})")
            icon_path = item.image_reference()
            if icon_path:
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(INVENTORY_ICON_SIZE)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)  # Une seule ligne sélectionnable à la fois
            btn.setStyleSheet(
                "QPushButton {"
                "  text-align: left;"
                "  padding: 4px 8px;"
                "  border: none;"
                "  background: transparent;"
                "}"
                "QPushButton:checked {"
                "  background-color: #3498db;"
                "  color: white;"
                "  border-radius: 4px;"
                "}"
            )
            btn.toggled.connect(lambda checked, r=row: self._select_inventory_row(r) if checked else None)
            layout.insertWidget(row, btn)  # insère avant le stretch

            # Restaure la sélection si elle est encore valide après le rafraîchissement
            if row == self._selected_inventory_row:
                btn.setChecked(True)

    def _refresh_skill_grid(self):
        """
        Reconstruit entièrement l'affichage de la liste de sorts dans la
        QScrollArea dédiée : une liste verticale (du haut vers le bas, une
        seule colonne) de sorts sélectionnables.
        Le bouton "Remove skill" retire le sort sélectionné.
        """
        layout = self._skill_list_layout

        # Vide le layout (en conservant le stretch final)
        while layout.count() > 1:
            child = layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        # Vide la description tant qu'aucune sélection n'est restaurée
        self.ui.skill_desc_display.clear()

        # Reconstruit une ligne par sort, du haut vers le bas
        for row, skill in enumerate(self._character_skills):
            btn = QPushButton(skill.name())
            icon_path = skill.image_reference()
            if icon_path:
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(INVENTORY_ICON_SIZE)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)  # Une seule ligne sélectionnable à la fois
            btn.setStyleSheet(
                "QPushButton {"
                "  text-align: left;"
                "  padding: 4px 8px;"
                "  border: none;"
                "  background: transparent;"
                "}"
                "QPushButton:checked {"
                "  background-color: #3498db;"
                "  color: white;"
                "  border-radius: 4px;"
                "}"
            )
            btn.toggled.connect(lambda checked, r=row: self._select_skill_row(r) if checked else None)
            layout.insertWidget(row, btn)  # insère avant le stretch

            # Restaure la sélection si elle est encore valide après le rafraîchissement
            if row == self._selected_skill_row:
                btn.setChecked(True)

    #---------Réinitialisation d'objet----------#

    # ----------------------------------------------------------------
    # Chat/Log
    # ----------------------------------------------------------------

    def _append_log(self, text: str):
        """
        Ajoute une ligne au bas de la zone de logs et fait défiler
        automatiquement vers la dernière ligne.

        :param text: Ligne de texte à afficher (déjà décodée en str).
        """
        self.ui.log_view.append(text)   # Insère la ligne à la fin du QTextEdit

        # Fait défiler la barre verticale jusqu'à sa position maximale
        # pour toujours afficher la ligne la plus récente.
        sb = self.ui.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def switch_log_display_state(self):
        # Cache le chat
        self.ui.actionLog_Chat.toggled.disconnect(self.switch_log_display_state)
        if(self.ui.log_view.isVisible() == True):
            self.ui.log_view.setVisible(False)
            self.ui.log_view_top.setVisible(False)
            if(self.ui.actionLog_Chat.isChecked() == True):
                self.ui.actionLog_Chat.setChecked(False)

        # Affiche le chat
        elif(self.ui.log_view.isVisible() == False):
            self.ui.log_view.setVisible(True)
            self.ui.log_view_top.setVisible(True)
            if(self.ui.actionLog_Chat.isChecked() == False):
                self.ui.actionLog_Chat.setChecked(True)

        else:
            print("Erreur switch log_view display")

        self.ui.actionLog_Chat.toggled.connect(self.switch_log_display_state)

    # ----------------------------------------------------------------
    # Map
    # ----------------------------------------------------------------

    def build_blueprint(self, name):
        grid = self._world
        blueprint = Blueprint(
            grid.n,
            grid.n,
            name
        )
        for cell in grid.atoms:
            x, y = cell._coord
            bp_cell = blueprint.get_cell(x, y)    
            if getattr(cell, "Path", None):
                bp_cell.new_reference(cell.Path)
            if getattr(cell, "PropPath", None):
                prop = Prop("Prop")
                prop.new_reference(cell.PropPath)
                bp_cell.add_content(prop)
    
        return blueprint
        
    def apply_blueprint_to_grid(self, blueprint):
        """
        Redimensionne la grille affichée pour correspondre à la taille
        du blueprint chargé, puis y applique l'image de chaque cellule.

        La grille (Grid) ne gère que des cases carrées (n x n) : si le
        blueprint n'est pas carré, on redimensionne au plus grand des
        deux côtés pour ne perdre aucune cellule, et on prévient dans
        les logs.
        """
        n = blueprint.length()
        if blueprint.width() != n:
            n = max(blueprint.length(), blueprint.width())
            self._append_log(
                "[ATTENTION] Le blueprint n'est pas carré "
                f"({blueprint.length()}x{blueprint.width()}) : la grille "
                f"a été redimensionnée en {n}x{n}."
            )

        # Reconstruit la grille à la bonne taille. _build_grid() crée une
        # grille neuve (donc déjà vide) : pas besoin de la nettoyer avant.
        self._build_grid(n, self._world.s_cell)

        for x in range(blueprint.length()):
            for y in range(blueprint.width()):
                bp_cell = blueprint.get_cell(x, y)
                visual_cell = self._world.atoms[
                    y * self._world.n + x
                ]
                image = bp_cell.image_reference()
                if image:
                    visual_cell.setImage(image)
                contents = bp_cell.contents()
                if contents:
                    prop_image = contents[0].image_reference()
                    if prop_image:
                        visual_cell.setProp(prop_image)

    # ----------------------------------------------------------------
    # Fonctions pour manipuler le style de la page et des boutons
    # ----------------------------------------------------------------

    def changeAppTheme(self):
        """
        Change le thème de l'application
        """ 
        current_theme = self.settings.value("THEME")
        selected_theme = self.ui.theme_list.currentText()
        if current_theme != selected_theme:
            self.settings.setValue("THEME", selected_theme)
            QAppSettings.updateAppSettings(self.main, reloadJson=True)
            if selected_theme == "Dark":
                self._apply_dark_theme()
            else:
                self._apply_light_theme()

    def _update_server_label_open(self):
        """
        Met à jour l'affichage pour l'état du serveur.

        """
        self.ui.server_state_label.setText("Server: open")
        self.ui.server_state_label.setStyleSheet("color: #2ecc71; font-size: 13px;")

    def _update_server_label_close(self):
        """
        Met à jour l'affichage pour l'état du serveur.

        """
        self.ui.server_state_label.setText("Server: closed")
        self.ui.server_state_label.setStyleSheet("color: #e74c3c; font-size: 13px;")

    # Inutilisé
    def _set_status(self, message: str, color: str):
        """
        Met à jour le texte et la couleur de la barre d'état en bas de la fenêtre.

        :param message: Texte à afficher dans la barre d'état.
        :param color:   Code couleur hexadécimal CSS (ex. "#2ecc71" pour vert).
        """
        # Applique un style QSS pour colorer et mettre en gras le message
        #self._status_bar.setStyleSheet(f"color: {color}; font-weight: bold;")
        # showMessage() remplace le contenu actuel de la barre d'état
        #self._status_bar.showMessage(message)
        pass

    def _apply_dark_theme(self):
        """
        Applique un thème sombre cohérent à l'ensemble de la fenêtre.

        Deux mécanismes complémentaires sont utilisés :
          1. QPalette : définit les couleurs systèmes Qt (fond, texte, liens…)
             appliquées automatiquement à tous les widgets enfants.
          2. setStyleSheet() : feuille de style QSS pour affiner des composants
             spécifiques que la palette ne couvre pas finement.
        """
        palette = QPalette()

        # Fond principal de la fenêtre (espace derrière les widgets)
        palette.setColor(QPalette.ColorRole.Window,        QColor("#161b22"))

        # Texte affiché sur le fond de la fenêtre (labels, titres…)
        palette.setColor(QPalette.ColorRole.WindowText,    QColor("#e6edf3"))

        # Fond des champs de saisie et zones de texte (QTextEdit, QLineEdit…)
        palette.setColor(QPalette.ColorRole.Base,          QColor("#0d1117"))

        # Fond alterné dans les listes et tableaux (lignes paires/impaires)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#1c2128"))

        # Fond et texte des infobulles (tooltips)
        palette.setColor(QPalette.ColorRole.ToolTipBase,   QColor("#1c2128"))
        palette.setColor(QPalette.ColorRole.ToolTipText,   QColor("#e6edf3"))

        # Texte dans les champs de saisie et zones de texte
        palette.setColor(QPalette.ColorRole.Text,          QColor("#e6edf3"))

        # Fond et texte des boutons Qt natifs (non-stylisés par QSS)
        palette.setColor(QPalette.ColorRole.Button,        QColor("#21262d"))
        palette.setColor(QPalette.ColorRole.ButtonText,    QColor("#e6edf3"))

        # Couleur des liens hypertexte (QLabel avec setOpenExternalLinks)
        palette.setColor(QPalette.ColorRole.Link,          QColor("#58a6ff"))

        self.main.setPalette(palette)   # Applique la palette à la fenêtre et à ses enfants

        # Feuille de style QSS complémentaire pour les composants spécifiques
        self.main.setStyleSheet(
            "QMainWindow { background-color: #161b22; }"
            "QStatusBar  { background-color: #0d1117; border-top: 1px solid #30363d; }"
            "QLabel      { color: #e6edf3; }"
            "QTextEdit   { background-color: #0d1117; color: #e6edf3; border: 1px solid #30363d; }"
            "QComboBox   { background-color: #21262d; color: #e6edf3; border: 1px solid #30363d; }"
            "QComboBox QAbstractItemView { background-color: #1c2128; color: #e6edf3; selection-background-color: #30363d; }"
        )

        # Force le fond + texte du panneau central et du stacked_widget
        self.ui.center_menu.setAutoFillBackground(True)
        self.ui.center_menu.setStyleSheet(
            "QWidget#center_menu { background-color: #161b22; }"
            "QWidget#center_menu QLabel    { color: #e6edf3; }"
            "QWidget#center_menu QComboBox { background-color: #21262d; color: #e6edf3; border: 1px solid #30363d; }"
            "QComboBox QAbstractItemView   { background-color: #1c2128; color: #e6edf3; selection-background-color: #30363d; }"
        )
        self.ui.stacked_widget.setStyleSheet(
            "QStackedWidget { background-color: #161b22; }"
        )

        # Custom_Widgets réapplique son style APRÈS cette fonction (via la boucle
        # d'événements Qt). On utilise QTimer.singleShot(0) pour s'exécuter après
        # que CW ait terminé — c'est le seul moyen fiable de garder le dernier mot.
        def _force_dark_text():
            for btn in [
                self.ui.character_btn, self.ui.map_btn, self.ui.server_btn,
                self.ui.settings_btn, self.ui.information_btn, self.ui.help_btn,
            ]:
                s = btn.styleSheet()
                # Remplace ou ajoute la couleur de texte directement dans le style inline
                if "color:" in s:
                    import re
                    s = re.sub(r'color\s*:\s*[^;]+;', 'color: #fefefe;', s)
                else:
                    s = s.rstrip() + " color: #fefefe;"
                btn.setStyleSheet(s)

        QTimer.singleShot(0, _force_dark_text)
        
    def _apply_light_theme(self):
        """
        Applique un thème clair cohérent à l'ensemble de la fenêtre.

        Même logique que _apply_dark_theme : QPalette pour les couleurs
        système Qt, puis QSS pour affiner certains composants.
        """
        palette = QPalette()

        # Fond principal de la fenêtre (espace derrière les widgets)
        palette.setColor(QPalette.ColorRole.Window,        QColor("#f5f6f8"))

        # Texte affiché sur le fond de la fenêtre (labels, titres…)
        palette.setColor(QPalette.ColorRole.WindowText,    QColor("#1c1f24"))

        # Fond des champs de saisie et zones de texte (QTextEdit, QLineEdit…)
        palette.setColor(QPalette.ColorRole.Base,          QColor("#ffffff"))

        # Fond alterné dans les listes et tableaux (lignes paires/impaires)
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#eceef1"))

        # Fond et texte des infobulles (tooltips)
        palette.setColor(QPalette.ColorRole.ToolTipBase,   QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.ToolTipText,   QColor("#1c1f24"))

        # Texte dans les champs de saisie et zones de texte
        palette.setColor(QPalette.ColorRole.Text,          QColor("#1c1f24"))

        # Fond et texte des boutons Qt natifs (non-stylisés par QSS)
        palette.setColor(QPalette.ColorRole.Button,        QColor("#e6e8eb"))
        palette.setColor(QPalette.ColorRole.ButtonText,    QColor("#1c1f24"))

        # Couleur des liens hypertexte (QLabel avec setOpenExternalLinks)
        palette.setColor(QPalette.ColorRole.Link,          QColor("#2563eb"))

        self.main.setPalette(palette)   # Applique la palette à la fenêtre et à ses enfants

        # Feuille de style QSS complémentaire pour les composants spécifiques
        # NOTE : QPushButton est explicitement stylé ici car Custom_Widgets
        # applique son propre QSS (issu du JSON de thème) qui peut laisser
        # un texte clair sur fond clair après reloadJson=True -> boutons
        # invisibles. On force donc fond + texte + hover + disabled.
        self.main.setStyleSheet(
            "QMainWindow { background-color: #f5f6f8; }"
            "QStatusBar  { background-color: #ffffff; border-top: 1px solid #d0d4d9; }"
            "QLabel      { color: #1c1f24; }"
            "QTextEdit   { background-color: #ffffff; color: #1c1f24; border: 1px solid #d0d4d9; }"
            "QComboBox   { background-color: #e6e8eb; color: #1c1f24; border: 1px solid #d0d4d9; }"
            "QPushButton {"
            "  background-color: #e6e8eb;"
            "  color: #1c1f24;"
            "  border: 1px solid #d0d4d9;"
            "  border-radius: 6px;"
            "  padding: 6px 10px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #d8dbdf;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #c6cad0;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #f0f1f3;"
            "  color: #9aa0a8;"
            "}"
            "QComboBox QAbstractItemView { background-color: #ffffff; color: #1c1f24; selection-background-color: #d8dbdf; }"
        )

        # Force le fond + texte + widgets du panneau central
        self.ui.center_menu.setAutoFillBackground(True)
        self.ui.center_menu.setStyleSheet(
            "QWidget#center_menu { background-color: #f5f6f8; }"
            "QWidget#center_menu QLabel    { color: #1c1f24; }"
            "QWidget#center_menu QFrame    { background-color: #eceef1; }"
            "QWidget#center_menu QComboBox { background-color: #e6e8eb; color: #1c1f24; border: 1px solid #d0d4d9; }"
            "QComboBox QAbstractItemView   { background-color: #ffffff; color: #1c1f24; selection-background-color: #d8dbdf; }"
            "QWidget#center_menu QPushButton { background-color: #e6e8eb; color: #1c1f24; border: 1px solid #d0d4d9; border-radius: 6px; padding: 6px 10px; }"
            "QWidget#center_menu QPushButton:hover    { background-color: #d8dbdf; }"
            "QWidget#center_menu QPushButton:pressed  { background-color: #c6cad0; }"
            "QWidget#center_menu QPushButton:disabled { background-color: #f0f1f3; color: #9aa0a8; }"
        )
        self.ui.stacked_widget.setStyleSheet(
            "QStackedWidget { background-color: #f5f6f8; }"
        )

        # Meme logique que le dark : Custom_Widgets ecrase le QSS global avec un
        # setStyleSheet inline par bouton. QTimer.singleShot s'execute apres CW.
        def _force_light_text():
            for btn in [
                self.ui.character_btn, self.ui.map_btn, self.ui.server_btn,
                self.ui.settings_btn, self.ui.information_btn, self.ui.help_btn,
            ]:
                s = btn.styleSheet()
                if "color:" in s:
                    import re
                    s = re.sub(r'color\s*:\s*[^;]+;', 'color: #1c1f24;', s)
                else:
                    s = s.rstrip() + " color: #1c1f24;"
                btn.setStyleSheet(s)

        QTimer.singleShot(0, _force_light_text)

    @staticmethod
    def _btn_style(color_normal: str, color_hover: str) -> str:
        """
        Génère et retourne une feuille de style QSS (Qt Style Sheet) pour un
        bouton, avec trois états visuels : normal, survol (hover) et désactivé.

        :param color_normal: Couleur de fond à l'état normal (hex).
        :param color_hover:  Couleur de fond quand la souris survole le bouton (hex).
        :return: Chaîne QSS prête à passer à setStyleSheet().
        """
        return (
            # État normal : fond coloré, texte blanc, coins arrondis
            f"QPushButton {{"
            f"  background-color: {color_normal};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  font-size: 13px;"
            f"  padding: 0 14px;"
            f"}}"
            # État survol : couleur légèrement plus sombre (color_hover)
            f"QPushButton:hover {{"
            f"  background-color: {color_hover};"
            f"}}"
            # État désactivé : grisé pour indiquer que l'action n'est pas disponible
            f"QPushButton:disabled {{"
            f"  background-color: #444444;"
            f"  color: #888888;"
            f"}}"
        )

    def _open_game_interface(self):
        """
        Slot connecte au signal clicked du bouton "Open game interface".
        Ouvre la fenetre du mode MJ (MJ_gamemode.MainWindow) en tant que
        fenetre independante et lui injecte une COPIE de la grille active de la session.
        """
        if self._game_window is None:
            self._game_window = GameModeWindow()

        # Check if the current world exists
        world = getattr(self, '_world', None)
        if world is not None:
            from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene

            # 1. Create a duplicate scene for the gamemode to use
            new_scene = QGraphicsScene()
            new_scene.setSceneRect(0, 0, 700, 520)
            new_scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

            # 2. Recreate the wall and world items for the new scene
            new_wall = InvisibleWallLimit(new_scene)
            new_scene.addItem(new_wall)

            n = world.n
            s_cell = world.s_cell
            new_world = Grid(n, s_cell)

            # Apply the exact same structural flags used in _build_grid
            new_world.atoms[0].setName("TL")
            new_world.atoms[0].setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            new_world.atoms[n - 1].setName("TR")
            new_world.atoms[n - 1].setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            new_world.atoms[(n - 1) * n].setName("BL")
            new_world.atoms[(n - 1) * n].setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            new_world.atoms[(n - 1) * n + (n - 1)].setName("BR")
            new_world.atoms[(n - 1) * n + (n - 1)].setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

            new_scene.addItem(new_world)

            # 3. Clone the visual configuration using a temporary blueprint
            blueprint = self.build_blueprint("temp_gamemode")
            for x in range(blueprint.length()):
                for y in range(blueprint.width()):
                    bp_cell = blueprint.get_cell(x, y)
                    visual_cell = new_world.atoms[y * new_world.n + x]
                    # 1. Copy the base cell image
                    image = bp_cell.image_reference()
                    if image:
                        visual_cell.setImage(image)
                    # 2. Copy the prop (object placed on top)
                    contents = bp_cell.contents()
                    if contents:
                        prop_image = contents[0].image_reference()
                        if prop_image:
                            visual_cell.setProp(prop_image)

            # 4. Inject the independent, duplicated map into the gamemode
            self._game_window.set_map(new_scene, new_world, new_wall)

        self._game_window.setWindowTitle("Dungeon Kitchen")
        self._game_window.setWindowIcon(QIcon("icon.png"))
        self._game_window.show()
        self._game_window.raise_()
        self._game_window.activateWindow()

    # ----------------------------------------------------------------
    # Gestion de l'événement de fermeture de la fenêtre
    # ----------------------------------------------------------------

    def closeEvent(self, event):
        """
        Surcharge de l'événement Qt déclenché quand l'utilisateur ferme la fenêtre
        (clic sur la croix, Alt+F4, Cmd+Q…).

        Sans cette surcharge, fermer la fenêtre laisserait le processus PHP
        tourner en arrière-plan (processus orphelin). On s'assure ici d'arrêter
        proprement le serveur et le thread de logs avant de fermer.

        :param event: QCloseEvent transmis par Qt ; on l'accepte pour confirmer la fermeture.
        """
        self._stop_server()   # Arrête le thread de logs et le processus PHP
        try:
            event.accept()        # Confirme la fermeture → la fenêtre est détruite
        except:
            exit()

    # ----------------------------------------------------------------
    # Gestion de save/load
    # ----------------------------------------------------------------

    #-----------Sauvegarde------------#
    def save_character_stat(self):
        """
        Sauvegarde les informations du personnage 
        dans un fichier XML
        """
        # Récolte du nom du personnage
        name = self.ui.character_name.toPlainText().strip()
        if not name:
            name = "Unnamed"

        # Récolte des attributs
        is_npc = self.ui.isNPC.isChecked()

        hp  = self.ui.hp_nb.value()
        str = self.ui.str_nb.value()
        dex = self.ui.dex_nb.value()
        con = self.ui.con_nb.value()
        int = self.ui.int_nb.value()
        wis = self.ui.wis_nb.value()
        cha = self.ui.cha_nb.value()

        # Vérifie si l'entité est un NPC ou un PC
        if is_npc:
            alignement = self.ui.alignement_NPC.currentIndex()
            sheet = NPC(Name=name, Alignement=alignement)
            save_dir = "./local/Sheets/NPC/"
        else:
            sheet = PC(Name=name)
            save_dir = "./local/Sheets/PC/"

        # Ajoute les attibuts sur la fiche de personnage
        sheet.add_stat("HP",  hp)
        sheet.add_stat("STR", str)
        sheet.add_stat("DEX", dex)
        sheet.add_stat("CON", con)
        sheet.add_stat("INT", int)
        sheet.add_stat("WIS", wis)
        sheet.add_stat("CHA", cha)

        # Ajoute les objets de l'inventaire en cours d'édition sur la fiche
        for item in self._inventory_items:
            sheet.addItem(item)

        # Ajoute les sorts en cours d'édition sur la fiche
        for skill in self._character_skills:
            sheet.addSkill(skill)

        # Associe l'icône du personnage à la fiche si une image a été choisie
        if self._character_icon_path and hasattr(sheet, 'new_reference'):
            sheet.new_reference(self._character_icon_path)

        # Création du fichier XML
        os.makedirs(save_dir, exist_ok=True)
        toXML_saveto(sheet, save_dir)

        self.pc_sheet = sheet  # keep reference if needed elsewhere
        self._append_log(f"[INFO] Personnage '{name}' sauvegardé dans {save_dir}")
    
    def save_item(self):
        """
        Sauvegarde les informations de l'objet.
        - Mode édition (depuis l'inventaire du personnage) : met à jour
          uniquement l'entrée en mémoire, sans toucher au fichier XML sur
          le disque, puis revient au menu Character.
        - Mode création : sauvegarde l'objet dans un fichier XML comme
          d'habitude.
        """
        # Récupère les informations de l'objet
        item_name = self.ui.item_name.text().strip()
        item_type = self.ui.item_type.currentText()
        item_description = self.ui.item_description.toPlainText().strip()
        item = self._build_item(item_name, item_type, item_description, self._item_image_path)

        if self._editing_item_index is not None:
            # Mode édition : mise à jour en mémoire uniquement
            self._inventory_items[self._editing_item_index] = item
            self._selected_inventory_row = self._editing_item_index
            self._editing_item_index = None
            self._refresh_inventory_grid()
            self.switch_to_character_menu()
            self._append_log(f"[INFO] Objet '{item_name}' mis à jour dans l'inventaire du personnage.")
        else:
            # Mode création : sauvegarde dans le fichier XML
            if item_type == "Weapon":
                save_dir = "./local/Items/Weapon/"
            elif item_type == "Armour":
                save_dir = "./local/Items/Armour/"
            elif item_type == "Consumable":
                save_dir = "./local/Items/Consumable/"
            else:
                save_dir = "./local/Items/Miscellaneous/"

            os.makedirs(save_dir, exist_ok=True)
            toXML_saveto(item, save_dir)
            self._append_log(f"[INFO] Objet '{item_name}' sauvegardé dans {save_dir}")

    def save_skill(self):
        """
        Sauvegarde les informations du sort.
        - Mode édition (depuis la liste de sorts du personnage) : met à jour
          uniquement l'entrée en mémoire, sans toucher au fichier XML sur
          le disque, puis revient au menu Character.
        - Mode création : sauvegarde le sort dans un fichier XML comme
          d'habitude.
        """
        # Récupère les informations du sort
        skill_name = self.ui.skill_name.text().strip()
        skill_description = self.ui.skill_description.toPlainText().strip()
        skill_type = self.ui.skill_category.currentText()
        skill = self._build_skill(skill_name, skill_type, skill_description, self._skill_image_path)

        if self._editing_skill_index is not None:
            # Mode édition : mise à jour en mémoire uniquement
            self._character_skills[self._editing_skill_index] = skill
            self._selected_skill_row = self._editing_skill_index
            self._editing_skill_index = None
            self._refresh_skill_grid()
            self.switch_to_character_menu()
            self._append_log(f"[INFO] Sort '{skill_name}' mis à jour dans la liste de sorts du personnage.")
        else:
            # Mode création : sauvegarde dans le fichier XML
            save_dir = "./local/skills/"
            os.makedirs(save_dir, exist_ok=True)
            toXML_saveto(skill, save_dir)
            self._append_log(f"[INFO] Sort '{skill_name}' sauvegardé dans {save_dir}")

    def save_map(self):
        name, ok = QInputDialog.getText(
            self.main,
            "Save Blueprint",
            "Blueprint name:"
        )
        if not ok or not name:
            return
        BLUEPRINT_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True
        )
        blueprint = self.build_blueprint(name)
        filename = BLUEPRINT_DIRECTORY / f"{name}.xml"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(toXML(blueprint))
        self._append_log(
            f"[INFO] Blueprint saved : {filename}"
        )

    def save_actionmenu(self):
        """
        Action de sauvegarde pour l'action save dans le menubar
        """
        index = self.ui.stacked_widget.currentIndex()

        match index:
            case 1: # Character
                self.save_character_stat()
            case 2: # Map
                self.save_map()
            case 6: # Item
                self.save_item()
            case 7: # skill
                self.save_skill()
            case _: # Default case
                self._append_log("Ne peut pas sauvegarder ces informations")

    # TODO
    def save_as_actionmenu(self):
        """
        Action de sauvegarde pour l'action save_as dans le menubar
        """
        #fileName = QFileDialog.getSaveFileName(None, "Save File", "", "(*.xml)")
        #print(fileName)   

    #-----------Chargement------------#
    def load_xml(self):
        """
        Charge un fichier XML et renvoie le chemin absolue du fichier
        """
        # Ouvre l'explorateur de fichier et 
        # récupère le chemin absolue du fichier
        fileName = QFileDialog.getOpenFileName( None, "Select File", "", "(*.xml)")
        object = fromXML(fileName[0])

        if(object == None):
            raise Exception("Erreur_file_selection")
        else:
            return object
    
    def load_character(self):
        """
        Charge la feuille d'un personnage et associe 
        les attributs, inventaire, sorts
        """
        sheet = self.load_xml()
        if not(isinstance(sheet,PC) or isinstance(sheet,NPC)):
            raise Exception("Invalid_object_type (Expecting character)")
        else:
            # Récupère les attributs
            name = sheet.name()
            hp  = sheet.get_stat("HP")
            str = sheet.get_stat("STR")
            dex = sheet.get_stat("DEX")
            con = sheet.get_stat("CON")
            int = sheet.get_stat("INT")
            wis = sheet.get_stat("WIS")
            cha = sheet.get_stat("CHA")

            # Assigne les attributs aux bons widgets
            self.ui.character_name.setText(name)
            self.ui.hp_nb.setValue(hp)
            self.ui.str_nb.setValue(str)
            self.ui.dex_nb.setValue(dex)
            self.ui.con_nb.setValue(con)
            self.ui.int_nb.setValue(int)
            self.ui.wis_nb.setValue(wis)
            self.ui.cha_nb.setValue(cha)

            # Restaure l'icône du personnage si elle est stockée dans la fiche
            icon_path = self._image_path_of(sheet) if hasattr(sheet, 'image_reference') else None
            self._character_icon_path = icon_path
            self._character_icon_label.setPixmap(
                QPixmap(icon_path) if icon_path else QPixmap(PLACEHOLDER_IMAGE)
            )

            # Déconnecte isNPC du signal
            self.ui.isNPC.blockSignals(True)
            
            # Vérifie si le personnage est un NPC ou un PC
            if(isinstance(sheet,NPC)):
                self.ui.isNPC.setChecked(True)
                self.ui.alignement_NPC.setCurrentIndex(sheet.alignement())
            else:
                self.ui.isNPC.setChecked(False)

            # Reconnecte isNPC du signal
            self.ui.isNPC.blockSignals(False)

            self.setNPC()

            # Récupère l'inventaire stocké dans la fiche et l'affiche
            self._inventory_items = list(sheet.inventory())
            self._selected_inventory_row = None
            self._refresh_inventory_grid()

            # Récupère les sorts stockés dans la fiche et les affiche
            self._character_skills = list(sheet.skills())
            self._selected_skill_row = None
            self._refresh_skill_grid()

            self.switch_to_character_menu()

    def load_item(self):
        """
        Charge un objet et affiche le nom,
        le titre et la description de l'objet
        dans le menu Item
        """
        item = self.load_xml()
        if not(isinstance(item,Item)):
            raise Exception("Invalid_object_type (Expecting item)")
        else:
            # Récupère les informations de l'objet
            item_name = item.name()
            item_type = item.type()
            item_description = item.description()

            # Assigne les attributs aux bons widgets
            self.ui.item_name.setText(item_name)
            self.ui.item_type.setCurrentText(item_type)
            self.ui.item_description.setText(item_description)
            self._item_image_path = self._image_path_of(item)
            self.ui.item_img.setPixmap(QPixmap(self._item_image_path or PLACEHOLDER_IMAGE))
            self.switch_to_item_menu()

    def load_skill(self):
        """
        Charge un sort et affiche le nom
        et la description du sort
        dans le menu skill
        """
        skill = self.load_xml()
        if not(isinstance(skill,Skill)):
            raise Exception("Invalid_object_type (Expecting skill)")
        else:
            # Récupère les informations du sort
            skill_name = skill.name()
            skill_description = skill.description()

            # Assigne les attributs aux bons widgets
            self.ui.skill_name.setText(skill_name)
            self.ui.skill_description.setText(skill_description)
            self._skill_image_path = self._image_path_of(skill)
            self.ui.skill_img.setPixmap(QPixmap(self._skill_image_path or PLACEHOLDER_IMAGE))

            self.switch_to_skill_menu()

    def load_add_cells_img_btns(self):
        dialog_add_img_cell = QDialog()
        dialog_add_img_cell.setWindowTitle("Image options")
        dialog_add_img_cell.setWindowIcon(QIcon("icon.png"))
        import_btn = QPushButton(parent=dialog_add_img_cell,text="Import image")
        divide_btn = QPushButton(parent=dialog_add_img_cell,text="Divide image")
        
        dialog_add_img_cell.setFixedSize(import_btn.width()+divide_btn.width()+40,import_btn.height()+40)
        import_btn.move(20,(import_btn.height()-10))
        divide_btn.move(import_btn.width()+25,(import_btn.height()-10))

        
        import_btn.clicked.connect(
            lambda: self.load_image(CELL_DIRECTORIES, self.ui.cells_image_list)
        )

        divide_btn.clicked.connect(
                    lambda: self.load_divider()
        )

        divide_btn.released.connect(dialog_add_img_cell.destroy)

        dialog_add_img_cell.exec()

    def load_divider(self):
        print(os.path.dirname(os.path.abspath(__file__)))
        filename, _ = QFileDialog.getOpenFileName(
            self.main,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif)"
        )
        if not filename:
            return
        dw = Divider_Window(64,filename,f"{os.path.dirname(os.path.abspath(__file__))}/../../Assets/Images/temp_dividing_img")
        dw.setWindowTitle("Dividing Bits")
        dw.setWindowIcon(QIcon("icon.png"))
        dw.show()
        dw.raise_()
        dw.activateWindow()    
        waiter = QEventLoop()
        dw.destroyed.connect(waiter.quit)
        waiter.exec()
        del dw
                            


    def load_image(self, directories, target_list):
        """
        Import an image into the local assets folder and refresh the list.
        directories:
            [Assets/..., local/Assets/...]
        target_list:
            cells_image_list or props_image_list
        """
        filename, _ = QFileDialog.getOpenFileName(
            self.main,
            "Select image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp *.PNG)"
        )
        if not filename:
            return
        
        source = Path(filename)
        # Always save in local folder
        local_dir = directories[-1]
        local_dir.mkdir(parents=True, exist_ok=True)
        destination = local_dir / source.name
        try:
            import shutil
            shutil.copy2(source, destination)
            self._append_log(
                f"[INFO] Image '{source.name}' copied to '{local_dir}'."
            )
            # Refresh list
            self._populate_image_list(target_list, directories)
            matches = target_list.findItems(
                source.name,
                Qt.MatchFlag.MatchExactly
            )
            if matches:
                target_list.setCurrentItem(matches[0])
        except Exception as exc:
            self._append_log(
                f"[ERREUR] Impossible d'ajouter l'image : {exc}"
            )

    def load_map(self):
        filename, _ = QFileDialog.getOpenFileName(
            self.main,
            "Load Blueprint",
            "local/Blueprint",
            "Blueprint (*.xml)"
        )
        if not filename:
            return
        blueprint = fromXML(filename,"Blueprint")
        self.apply_blueprint_to_grid(blueprint)
        self._append_log(
            f"[INFO] Blueprint loaded : {filename}"
        )

    # ----------------------------------------------------------------
    # Sauvegarde / chargement de session
    # ----------------------------------------------------------------

    def new_session(self):
        """
        Crée une nouvelle session vide : vide entièrement le dossier
        local/ (après confirmation) et y recrée l'arborescence de base
        attendue par l'application.

        La session active (self._current_session_path) est réinitialisée
        à None, puisqu'une nouvelle session n'a encore jamais été
        sauvegardée dans projects/.
        """
        confirm = QMessageBox.question(
            self.main,
            "Nouvelle session",
            f"Le contenu actuel de '{SESSION_LOCAL_DIRECTORY}' va être "
            "définitivement supprimé. Pensez à sauvegarder la session en "
            "cours si nécessaire. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            if SESSION_LOCAL_DIRECTORY.exists():
                shutil.rmtree(SESSION_LOCAL_DIRECTORY)
            for sub in SESSION_SUBFOLDERS:
                (SESSION_LOCAL_DIRECTORY / sub).mkdir(parents=True, exist_ok=True)
            self._current_session_path = None
            self._append_log(
                f"[INFO] Nouvelle session créée, '{SESSION_LOCAL_DIRECTORY}' a été réinitialisé."
            )
        except Exception as exc:
            self._append_log(
                f"[ERREUR] Impossible de créer une nouvelle session : {exc}"
            )
            return

        self._refresh_session_views()

    def update_session(self):
        """
        Met à jour la session active (la dernière session sauvegardée ou
        chargée via save_session()/load_session()) en remplaçant son
        contenu dans projects/ par celui du dossier local/ actuel.

        Si aucune session n'est active, invite l'utilisateur à utiliser
        "Sauvegarder la session" pour en créer une.
        """
        if self._current_session_path is None:
            self._append_log(
                "[INFO] Aucune session active à mettre à jour. "
                "Utilisez 'Sauvegarder la session' pour en créer une."
            )
            return

        if not SESSION_LOCAL_DIRECTORY.is_dir():
            self._append_log(
                f"[ERREUR] Dossier '{SESSION_LOCAL_DIRECTORY}' introuvable, rien à mettre à jour."
            )
            return

        confirm = QMessageBox.question(
            self.main,
            "Mettre à jour la session",
            f"La session '{self._current_session_path.name}' va être "
            "remplacée par le contenu actuel de "
            f"'{SESSION_LOCAL_DIRECTORY}'. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            if self._current_session_path.exists():
                shutil.rmtree(self._current_session_path)
            shutil.copytree(SESSION_LOCAL_DIRECTORY, self._current_session_path)
            self._append_log(
                f"[INFO] Session '{self._current_session_path.name}' mise à jour."
            )
        except Exception as exc:
            self._append_log(
                f"[ERREUR] Impossible de mettre à jour la session : {exc}"
            )

    def save_session(self):
        """
        Sauvegarde la session courante (tout le contenu du dossier
        local/) dans un nouveau dossier sous projects/.

        Séquence d'actions :
          1. Demande un nom de session à l'utilisateur.
          2. Évite d'écraser une session existante du même nom en
             ajoutant un suffixe "(1)", "(2)", ... si besoin.
          3. Copie récursivement local/ vers projects/<nom>/.
        """
        name, ok = QInputDialog.getText(
            self.main,
            "Sauvegarder la session",
            "Nom de la session :"
        )
        if not ok or not name:
            return

        SESSION_PROJECTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

        # Évite d'écraser une session existante portant le même nom
        destination = SESSION_PROJECTS_DIRECTORY / name
        suffix = 1
        base_name = name
        while destination.exists():
            name = f"{base_name}({suffix})"
            destination = SESSION_PROJECTS_DIRECTORY / name
            suffix += 1

        if not SESSION_LOCAL_DIRECTORY.is_dir():
            self._append_log(
                f"[ERREUR] Dossier '{SESSION_LOCAL_DIRECTORY}' introuvable, rien à sauvegarder."
            )
            return

        try:
            shutil.copytree(SESSION_LOCAL_DIRECTORY, destination)
            self._current_session_path = destination
            self._append_log(
                f"[INFO] Session sauvegardée dans '{destination}'"
            )
        except Exception as exc:
            self._append_log(
                f"[ERREUR] Impossible de sauvegarder la session : {exc}"
            )

    def load_session(self):
        """
        Charge une session sauvegardée depuis projects/ et remplace le
        contenu du dossier local/ par celui de la session choisie.

        Séquence d'actions :
          1. Ouvre un sélecteur de dossier dans projects/.
          2. Demande confirmation (le contenu actuel de local/ sera
             remplacé, donc perdu s'il n'a pas été sauvegardé).
          3. Supprime local/ puis copie le dossier de session choisi
             à sa place.
          4. Rafraîchit les listes d'images affichées dans l'interface.
        """
        SESSION_PROJECTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

        directory = QFileDialog.getExistingDirectory(
            self.main,
            "Charger une session",
            str(SESSION_PROJECTS_DIRECTORY)
        )
        if not directory:
            return

        source = Path(directory)

        confirm = QMessageBox.question(
            self.main,
            "Charger la session",
            f"Le contenu actuel de '{SESSION_LOCAL_DIRECTORY}' va être "
            "remplacé par la session sélectionnée. Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            if SESSION_LOCAL_DIRECTORY.exists():
                shutil.rmtree(SESSION_LOCAL_DIRECTORY)
            shutil.copytree(source, SESSION_LOCAL_DIRECTORY)
            self._current_session_path = source
            self._append_log(
                f"[INFO] Session '{source.name}' chargée dans '{SESSION_LOCAL_DIRECTORY}'"
            )
        except Exception as exc:
            self._append_log(
                f"[ERREUR] Impossible de charger la session : {exc}"
            )
            return

        self._refresh_session_views()

    def _refresh_session_views(self):
        """
        Rafraîchit les éléments de l'interface qui dépendent du contenu
        du dossier local/ (listes d'images des cellules et des props)
        après le chargement d'une session.
        """
        if hasattr(self.ui, "cells_image_list"):
            self._populate_image_list(
                self.ui.cells_image_list,
                CELL_DIRECTORIES
            )
        if hasattr(self.ui, "props_image_list"):
            self._populate_image_list(
                self.ui.props_image_list,
                PROP_DIRECTORIES
            )
        self.load_web_registered_pcs()
            
    def load_web_registered_pcs(self):
        """
        Scanne le dossier local/Players/ et local/Sheets/PC/ pour charger
        les nouveaux joueurs inscrits via le site web.
        """
        player_dir = Path("./local/Players")
        pc_dir = Path("./local/Sheets/PC")
        
        if not player_dir.exists() or not pc_dir.exists():
            return

        loaded_players = []
        
        # Charge tous les joueurs
        for xml_file in player_dir.glob("*.xml"):
            try:
                player_obj = fromXML(str(xml_file), Type="Player")
                loaded_players.append(player_obj)
                self._append_log(f"[WEB-SYNC] Joueur synchronisé : {player_obj.name()} (ID: {player_obj.ID()})")
                
                # Charge automatiquement la fiche personnage associée si elle existe
                pc_file_path = pc_dir / player_obj.pc_file()
                if pc_file_path.exists():
                    pc_obj = fromXML(str(pc_file_path), Type="PC")
                    player_obj.newRole(pc_obj)
                    self._append_log(f"[WEB-SYNC] Fiche personnage rattachée pour {player_obj.name()}")
                    
            except Exception as e:
                self._append_log(f"[ERREUR WEB-SYNC] Impossible de lire le joueur {xml_file.name} : {e}")