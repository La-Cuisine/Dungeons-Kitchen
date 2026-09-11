from __future__ import annotations

import sys
import os
import struct
import math
import time

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGraphicsItem,
    QVBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsProxyWidget,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QStyle,
    QFileDialog,
    QCheckBox,
    QDoubleSpinBox,       
    QLineEdit,
    QDialog,
    
)
from PySide6.QtCore import (
    Qt,
    QRectF, 
    QSize,
    QPointF,
    QEventLoop,
)
from PySide6.QtGui import (
    QFont,
    QColor,
    QBrush,
    QPen,
    QPainter,
    QPainterPath,
    QResizeEvent,
    QPixmap,
    QImage,
    QImageWriter,
    QKeyEvent,
    QPainterPathStroker,
    QMovie,
    
) 


#----------!! READ-ME !!--------#
#-------!! CTRL+F 5432 !!-------#
#-------!! CTRL+F 7894 !!-------#
#----------!! READ-ME !!--------#

_destinate_folder = ""

backcolor = "#171717ff" 
_filename_prefix = ""
_verticle = False

_expand = False
img = None
img_W = -1
img_H = -1

_is_a_gif = False
_frame = -1

#Say if the step set (where the users choose the scale) is valid or not
_set_step_valid = False

_is_a_pattern = None

_background_set = False

_capturestart = False

_wall = None

_view_bounds = {"cw": 350.0, "ch": 260.0}

_col_cell = {"TL" : (None,None) , "TR" : (None,None) , "BL" : (None,None) , "BR" : (None,None) }

# ---------------------------------------------------------------------------
# une seule lecture + redimensionnement par (path, w, h)
# ---------------------------------------------------------------------------
_pixmap_cache: dict[tuple, QPixmap] = {}
_movie_cache: dict[tuple, QMovie] = {}
def _get_scaled_pixmap(path: str, w: int, h: int) -> QPixmap:
    key = (path, w, h)
    if key not in _pixmap_cache:
        _pixmap_cache[key] = QPixmap(path).scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
    return _pixmap_cache[key]

def _get_scaled_movie(path: str, w: int, h: int) -> QMovie:
    key = (path, w, h) 
    if key not in _movie_cache:
        _movie_cache[key] = QMovie(path)
        _movie_cache[key].setScaledSize(
            QSize(w*1.3, h)
        )

    return _movie_cache[key]

class Divider_Window(QMainWindow):
    def __init__(self, s_cell:int, pathing:str, destinate_folder : str):
        super().__init__()
        global img_W,img_H,_set_step_valid,_expand,img,_destinate_folder
        set = popup_resize(pathing)
        waiter = QEventLoop()
        set.destroyed.connect(waiter.quit)
        waiter.exec()
        ############################    
        if _set_step_valid == True :

            _destinate_folder = destinate_folder
            self.s_cell = s_cell
            nx = math.ceil(img_W/s_cell)
            ny = math.ceil(img_H/s_cell)

            #self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.setWindowModality(Qt.WindowModality.ApplicationModal)

            self.setFixedSize(700, 520)
            self.move(QApplication.primaryScreen().geometry().center()- self.rect().center())
##############################################################
            #cree une scene graphique de taille 700x520 
            self.Interface = QGraphicsScene()
            self.Interface.setSceneRect(0,0,700, 520)
            # cree un espace de "visualisation"/"rendu" de la scene
            self.view = View_Interface_divise(self.Interface)
            self.view.setMouseTracking(True)
##############################################################

##############################################################
            self.img_scene = QGraphicsScene()
            self.img_scene.setSceneRect(0,0,384, 384)

            self.img_view = View_img(self.img_scene)
            self.img_view.setMouseTracking(True)

            self.graphwidget = QGraphicsProxyWidget() 
            self.graphwidget.setWidget(self.img_view)
            self.graphwidget.setPos(50, 40) 

##############################################################


            contain = QWidget()

            self.root_layout = QVBoxLayout(contain)
            #root_layout.setSpacing(12)
            self.root_layout.setContentsMargins(0, 0, 0, 0)        
            self.root_layout.addWidget(self.view)
            self.setCentralWidget(contain)


            global _wall
            _wall = InvisibleWallLimit(self.img_scene)
            _wall.setVisible(False)
            self.img_scene.addItem(_wall)


            self.img_space  = IMG_SPACE(pathing,nx,ny,s_cell)
            (self.img_space._atoms[0]).setName("TL")
            (self.img_space._atoms[0]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

            (self.img_space._atoms[nx - 1]).setName("TR")
            (self.img_space._atoms[nx - 1]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

            (self.img_space._atoms[(nx - 1) * ny]).setName("BL")
            (self.img_space._atoms[(nx - 1) * ny]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
            (self.img_space._atoms[(nx - 1) * ny + (ny - 1)]).setName("BR")
            (self.img_space._atoms[(nx - 1) * ny + (ny - 1)]).setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

            self.img_view.addItemNeeds(self.img_space)

            self.img_scene.addItem(self.img_space)

            self.Interface.addItem(self.graphwidget)

            self.view.setsubspace(self.graphwidget)

            self.button_captures = capture_button(self.view,self.Interface,self.img_space)
            
            if _expand == False :
                self._back_button = Bacground_button(self.view,self.Interface,self.img_space)  
                self._reset_back_button = Reset_Bacground_button(self.view,self.Interface,self.img_space)
                rotate_button(self.view,img,False)
                rotate_button(self.view,img,True)
            else :
                rotate_button(self.view,self.img_space,False)
                rotate_button(self.view,self.img_space,True)
            
                
            #self.img_space.captures()

#5432 MAYBE THIS NEED TO BE MODIFY WHEN IMPLEMENT IN THE SOFTWARE (modify was make there is no longer problem here)        
    def show(self):
        global _set_step_valid
        if _set_step_valid == False :
            self.close()
    
        else:  
            return super().show()
        

# View of the IMG Space
class View_img(QGraphicsView):

    zoomfac = 1.15
    zoomMax = 2.5
    zoomMin = 0.5

    def __init__(self, scene):
        super().__init__(scene)
        global backcolor
        self._grid = None
        self._shift_press = False

        
        self.zoom = 1.0
        self._fitted_once = False

        

        self._Items_needs = []

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(QBrush(QColor(backcolor)))
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        #  mise à jour viewport limitée à la zone modifiée (pas toute la vue)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate
        )

    def _update_world_bounds(self):
        global _wall, _view_bounds

        if self.scene() is None:
            return

        visible = self.mapToScene(self.viewport().rect()).boundingRect()
        _view_bounds["cw"] = visible.center().x()
        _view_bounds["ch"] = visible.center().y()

        if _wall is not None:
            _wall.sizeUpdate(visible)

    
    def addItemNeeds(self, item : QGraphicsItem):
        self._Items_needs.append(item)

    def keyPressEvent(self, event):
        global img
        if event.key() == Qt.Key.Key_Shift:
            self._shift_press = True

        if img is not None:
            if img.isSelected() :
                if event.key() in (Qt.Key.Key_Up,Qt.Key.Key_Down,Qt.Key.Key_Left,Qt.Key.Key_Right):
                    event.ignore()
                    return
                
        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
            if event.key() == Qt.Key.Key_Shift:
                self._shift_press = False
            return super().keyReleaseEvent(event)
        

        
    
    #def mousePressEvent(self, event):
    #    view_pt = event.position().toPoint()
#
#
    #    # activer le movable ici (une seule fois par clic).
    #    # On remonte la hiérarchie pour gérer tous les cas :
    #    #   fond Grid          → item est Grid
    #    #   cellule sans image → item est Interface_Cell, parent est Grid
    #    #   cellule avec image → item est Img, parent est Interface_Cell, grand-parent est Grid
    #    item = self.itemAt(view_pt)
    #    candidate = item
    #    while candidate is not None and (not isinstance(candidate,IMG)):
    #        if isinstance(candidate, IMG_SPACE):
    #            candidate.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
    #            self._grid = candidate
    #            break
    #        candidate = candidate.parentItem()
#
#
    #    return super().mousePressEvent(event)
    #
    #def mouseReleaseEvent(self, event):
    #    # désactiver le movable au relâchement
    #    if self._grid is not None:
    #        self._grid.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
    #    return super().mouseReleaseEvent(event)


    # zoom non au point
    def wheelEvent(self, event):


        if self._shift_press:
            angle = event.angleDelta().y()
            if angle == 0:
                event.accept()
                return

            factor = self.zoomfac if angle > 0 else 1 / self.zoomfac
            new_zoom = max(self.zoomMin, min(self.zoomMax, self.zoom * factor))
            applied = new_zoom / self.zoom

            if applied != 1.0:
                self.zoom = new_zoom

                cursor_scene = self.mapToScene(event.position().toPoint())
                self.scale(applied, applied)
                cursor_scene_after = self.mapToScene(event.position().toPoint())
                delta = cursor_scene_after - cursor_scene
                self.translate(delta.x(), delta.y())

                self._update_world_bounds()

            event.accept()
            return

        return super().wheelEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        if not self._fitted_once and self.scene() is not None:
            self.fitInView(
                self.scene().sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            )
            self.zoom = self.transform().m11()
            self._fitted_once = True

        self._update_world_bounds()
        # Repositionner l'overlay coordonnees apres chaque resize
        for it in self._Items_needs:
            if hasattr(it, "align"):
                it.align()
        super().resizeEvent(event)


class InvisibleWallLimit(QGraphicsPathItem):
    """Croix de murs invisibles utilisee par Grid pour limiter le
    deplacement. Sa position/etendue suit desormais la zone REELLEMENT
    VISIBLE dans la vue (passee via sizeUpdate), et non plus le centre
    fixe de la sceneRect d'origine -> elle reste coherente quand on
    zoome ou qu'on redimensionne la fenetre."""

    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.setZValue(0)
        self.setPen(QPen(QColor("#8f8f8fff"), 2))
        self.setPos(0, 0)
        self.sizeUpdate(scene.sceneRect())

    def sizeUpdate(self, visible_rect: QRectF):
        cx = visible_rect.center().x()
        cy = visible_rect.center().y()
        span_w = max(visible_rect.width(), 1.0) * 4
        span_h = max(visible_rect.height(), 1.0) * 4

        walls = QPainterPath()
        walls.addRect(cx, cy - span_h / 2, 1, span_h)
        walls.addRect(cx - span_w / 2, cy, span_w, 1)
        self.setPath(walls)

#Window view + keypress movement of the img
class View_Interface_divise(QGraphicsView):

    _key_ctrl_press = False

    def __init__(self, scene : QGraphicsScene):
        super().__init__(scene)
        global backcolor,_expand
        self._subspace = None
        self._Items_needs = []
        if _expand == False :
            DesignSquare(self,120,340)
            self.positons = Space_Positions(self,scene)
        else :
            tmp = DesignSquare(self,120,150)
            tmp.move((self.width()-tmp.width())-10,140)
        TextBoxesNameFile(self)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(backcolor)))
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

    def addItemNeeds(self, item : QGraphicsItem):
        self._Items_needs.append(item)

    def setsubspace(self,subview : QGraphicsProxyWidget):
        self._subspace = subview
    
    def mousePressEvent(self, event):
        global img
        if self._key_ctrl_press == True:
            img.setSelected(False)
            img.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,False)
            img.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,False)
            img.parentItem().setSelected(True)
            
        else:
            img.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,True)
            img.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,True)            
            if img is not None :
                if not img.isUnderMouse():
                    img.setSelected(False)
                else : 
                    self.positons.unpress()

        return super().mousePressEvent(event)


    
    def keyPressEvent(self, event):
        global img
        if event.key() == Qt.Key.Key_Control:
            self._key_ctrl_press = True
        else:
            if img is not None :
                if img.isSelected() : 
                    if event.key() == Qt.Key.Key_Left:
                        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                            img.setX(img.x()-0.5)
                        else:
                            img.setX(img.x()-3)
                    if event.key() == Qt.Key.Key_Right:
                        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                            img.setX(img.x()+0.5)
                        else:
                            img.setX(img.x()+3)
                    if event.key() == Qt.Key.Key_Up:
                        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                            img.setY(img.y()-0.5)
                        else:
                            img.setY(img.y()-3)
                    if event.key() == Qt.Key.Key_Down:
                        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                            img.setY(img.y()+0.5)
                        else:
                            img.setY(img.y()+3)

        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Control:
            self._key_ctrl_press = False
        return super().keyReleaseEvent(event)

    def resizeEvent(self, event):
        self.fitInView(
            self.scene().sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        )
                    
        return super().resizeEvent(event)
    
#the grid compose of little square
class IMG_SPACE(QGraphicsRectItem):
    def __init__(self, path : str,  nx : int,ny : int, s_cell : int):
        super().__init__(0, 0, nx * s_cell, ny * s_cell)
        global img_W, img_H, img, _expand, _destinate_folder
        self.tmpfold = _destinate_folder
        self.nx = nx
        self.ny = ny
        self.w = nx * s_cell
        self.h = ny * s_cell
        self.s_cell = s_cell
        self._img = None
        self.setZValue(0)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemContainsChildrenInShape,True)
        ###########################################################################
        #  GOAT : Empeche les enfants d'avoir un rendu en dehors du parent        #
        #           Donc empeche les hallucinations de rendu                      #
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,True)
        ###########################################################################
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setPen(Qt.PenStyle.NoPen)
                
        #self.setPos(78,50)
        for i in range(ny):
            for j in range(nx):
                backcell = Interface_Cell(s_cell * j, s_cell * i, s_cell, s_cell,True) 
                cell = Interface_Cell(s_cell * j, s_cell * i, s_cell, s_cell,False)
                backcell.setParentItem(self)
                cell.setParentItem(self)
                backcell.setCoord(j,i)
                cell.setCoord(j,i)

        if _expand == False :      
            self.img_rect = IMG(path,img_W,img_H,self)
            img = self.img_rect
        else : 
            self.img_rect = None
            self.setimage(path,False)
        self._atoms = [item for item in self.childItems() if isinstance(item, Interface_Cell) if item.getBackCell() == False]
        self._backcell = [item for item in self.childItems() if isinstance(item, Interface_Cell) if item.getBackCell() == True]
        self._gpos = QPointF(0, 0)


    
    def captures(self) :
        global _capturestart, _filename_prefix,_destinate_folder
        _capturestart = True
        if self.img_rect is not None :
            self.img_rect.setVisible(False)
        if not _filename_prefix or not _filename_prefix.strip() :
            folder = f"{time.strftime("%Y%m%d_%H%M%S")}"
            os.makedirs(f"{self.tmpfold}/{folder}")
            _destinate_folder = f"{self.tmpfold}/{folder}"
        else : 
            os.makedirs(f"{self.tmpfold}/{_filename_prefix}")
            _destinate_folder = f"{self.tmpfold}/{_filename_prefix}"
        for it in self._atoms:
            if it.capture() == False:
                qd = QDialog()
                qd.setWindowTitle("Error: File Writing")
                message = QLabel(parent=qd,text="Storage Full \nor Folder in Read-Only \nor Device was closed")
                message.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignJustify )
                message.adjustSize()
                qd.setFixedSize(message.width()+40,message.height()+40)
                message.move(20,(message.height()-20)/2)
                qd.exec()
                del qd
                del message
                break
        _capturestart = False

    def getsize(self):
        return (self.w,self.h)

    def setimage(self,path : str , mode : bool | None):
        if mode is None :
            return
        if mode == True :    
            self.removeimage()
            for item in self._backcell:
                item.setImage(path)
        if mode == False :
            self.removeimage()
            self.Path = path
            self._img = QGraphicsPixmapItem()
            self._img.setPixmap(QPixmap(path))
            # utilise le cache au lieu de recharger depuis le disque
            scaled = _get_scaled_pixmap(path, self.w, self.h)
            # Ne retirer de la scène que si l'item y est déjà (pixmap non null = déjà posé)
            if not self._img.pixmap().isNull() and self._img.scene() is not None:
                self._img.scene().removeItem(self._img)
            self._img.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            self._img.setPixmap(scaled)
            w = self._img.pixmap().width() 
            h = self._img.pixmap().height()
            self._img.setPixmap(self._img.pixmap().copy(abs(self.w/2 - w/2),abs(self.h/2 - h/2),self.w,self.h))
            self._img.setParentItem(self)
            self._img.setPos(0,0)
            self._img.setTransformOriginPoint(self._img.boundingRect().center())
            self.update()
        
    def isimg(self):
        if self._img is not None :
            return True
        else : 
            return False
        
    def getimg(self) : 
        return self._img

    def removeimage(self):
        global _background_set
        if _background_set == True:
            for item in self._backcell:
                item.removeimg()
            _background_set = False
        elif self._img is not None:            
            self.scene().removeItem(self._img)
            del self._img
            self._img = None


    def itemChange(self, change, value):
    
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            global _col_cell
            global _wall
            global _view_bounds
            new_pos = value
            old_pos = self.pos()
            lx = self.nx
            ly = self.ny
            b = []
            b.append(self._atoms[0])
            b.append(self._atoms[lx - 1])
            b.append(self._atoms[(lx - 1) * ly])
            b.append(self._atoms[(lx - 1) * ly + (ly - 1)])

            cw = _view_bounds["cw"]
            ch = _view_bounds["ch"]

            for i in range(len(b)):
                if b[i].getName() != "":
                    # une seule lecture/écriture par coin (était 2 avant)
                    prev = _col_cell[b[i].getName()][1]
                    _col_cell[b[i].getName()] = (prev, b[i].scenePos())

            for i in range(len(b)):
                if i == 0:
                    if not (b[i].scenePos().x() < cw - (self.nx * self.s_cell / 2) or b[i].scenePos().y() < ch - (self.ny * self.s_cell / 2)):
                        # QRectF + intersects() au lieu de QGraphicsRectItem temporaire
                        j = QRectF(b[i].scenePos().x(), b[i].scenePos().y(), b[i].rect().width(), b[i].rect().height())
                        if _wall.path().intersects(j):
                            return QPointF(min(old_pos.x(), new_pos.x()), min(old_pos.y(), new_pos.y()))

                        inter = self._sweep(b[i], i)
                        if inter is None:
                            return super().itemChange(change, value)
                        col = _wall.mapFromScene(_wall.shape())
                        if inter.intersects(col):
                            return QPointF(min(old_pos.x(), new_pos.x()), min(old_pos.y(), new_pos.y()))
                        if b[i].scenePos().x() >= cw + 8 or b[i].scenePos().y() >= ch + 8:
                            self.ungrabMouse()
                            return QPointF(self._gpos.x() + cw - self.s_cell, self._gpos.y() + ch - self.s_cell)

                elif i == 1:
                    if not (b[i].scenePos().x() + self.nx * self.s_cell - self.s_cell > cw + (self.nx * self.s_cell / 2) or b[i].scenePos().y() < ch - (self.ny * self.s_cell / 2)):
                        j = QRectF(b[i].scenePos().x() + self.nx * self.s_cell - self.s_cell, b[i].scenePos().y(), b[i].rect().width(), b[i].rect().height())
                        if _wall.path().intersects(j):
                            return QPointF(max(old_pos.x(), new_pos.x()), min(old_pos.y(), new_pos.y()))

                        inter = self._sweep(b[i], i)
                        if inter is None:
                            return super().itemChange(change, value)
                        col = _wall.mapFromScene(_wall.shape())
                        if inter.intersects(col):
                            return QPointF(max(old_pos.x(), new_pos.x()), min(old_pos.y(), new_pos.y()))
                        if b[i].scenePos().x() + self.nx * self.s_cell - self.s_cell <= cw - 8 or b[i].scenePos().y() >= ch + 8:
                            self.ungrabMouse()
                            return QPointF(self._gpos.x() + cw - (self.nx * self.s_cell - self.s_cell) + self.s_cell, self._gpos.y() + ch - self.s_cell)

                elif i == 2:
                    if not (b[i].scenePos().y() + self.ny * self.s_cell - self.s_cell > ch + (self.ny * self.s_cell / 2) or b[i].scenePos().x() < ch - (self.ny * self.s_cell / 2)):
                        j = QRectF(b[i].scenePos().x(), b[i].scenePos().y() + self.ny * self.s_cell - self.s_cell, b[i].rect().width(), b[i].rect().height())
                        if _wall.path().intersects(j):
                            return QPointF(min(old_pos.x(), new_pos.x()), max(old_pos.y(), new_pos.y()))

                        inter = self._sweep(b[i], i)
                        if inter is None:
                            return super().itemChange(change, value)
                        col = _wall.mapFromScene(_wall.shape())
                        if inter.intersects(col):
                            return QPointF(min(old_pos.x(), new_pos.x()), max(old_pos.y(), new_pos.y()))
                        if b[i].scenePos().x() >= cw + 8 or b[i].scenePos().y() + self.ny * self.s_cell - self.s_cell <= ch - 8:
                            self.ungrabMouse()
                            return QPointF(self._gpos.x() + cw - self.s_cell, self._gpos.y() + ch - (self.ny * self.s_cell - self.s_cell) + self.s_cell)

                elif i == 3:
                    if not (b[i].scenePos().y() + self.ny * self.s_cell - self.s_cell > ch + (self.ny * self.s_cell / 2) or b[i].scenePos().x() + self.nx * self.s_cell - self.s_cell > cw + (self.nx * self.s_cell / 2)):
                        j = QRectF(b[i].scenePos().x() + self.nx * self.s_cell - self.s_cell, b[i].scenePos().y() + self.ny * self.s_cell - self.s_cell, b[i].rect().width(), b[i].rect().height())
                        if _wall.path().intersects(j):
                            return QPointF(max(old_pos.x(), new_pos.x()), max(old_pos.y(), new_pos.y()))

                        inter = self._sweep(b[i], i)
                        if inter is None:
                            return super().itemChange(change, value)
                        col = _wall.mapFromScene(_wall.shape())
                        if inter.intersects(col):
                            return QPointF(max(old_pos.x(), new_pos.x()), max(old_pos.y(), new_pos.y()))
                        if b[i].scenePos().x() + self.nx * self.s_cell - self.s_cell <= cw - 8 or b[i].scenePos().y() + self.ny * self.s_cell - self.s_cell <= ch + 8:
                            self.ungrabMouse()
                            return QPointF(self._gpos.x() + cw - (self.nx * self.s_cell - self.s_cell) + self.s_cell, self._gpos.y() + ch - (self.ny * self.s_cell - self.s_cell) + self.s_cell)

            self.update()

        return super().itemChange(change, value)
    
    def _sweep(self, b: Interface_Cell, correction: int):
        global _col_cell

        w = b.rect().width() + 4   # rect() au lieu de boundingRect()
        h = b.rect().height() + 4
        if _col_cell.get(b.getName())[0] is None:
            return None
        if correction == 0:
            old_cell = QPointF(_col_cell.get(b.getName())[0].x(), _col_cell.get(b.getName())[0].y())
            new_cell = QPointF(_col_cell.get(b.getName())[1].x(), _col_cell.get(b.getName())[1].y())
        elif correction == 2:
            old_cell = QPointF(_col_cell.get(b.getName())[0].x(), _col_cell.get(b.getName())[0].y() + self.ny * self.s_cell - self.s_cell)
            new_cell = QPointF(_col_cell.get(b.getName())[1].x(), _col_cell.get(b.getName())[1].y() + self.ny * self.s_cell - self.s_cell)
        elif correction == 1:
            old_cell = QPointF(_col_cell.get(b.getName())[0].x() + self.nx * self.s_cell - self.s_cell, _col_cell.get(b.getName())[0].y())
            new_cell = QPointF(_col_cell.get(b.getName())[1].x() + self.nx * self.s_cell - self.s_cell, _col_cell.get(b.getName())[1].y())
        elif correction == 3:
            old_cell = QPointF(_col_cell.get(b.getName())[0].x() + self.nx * self.s_cell - self.s_cell, _col_cell.get(b.getName())[0].y() + self.ny * self.s_cell - self.s_cell)
            new_cell = QPointF(_col_cell.get(b.getName())[1].x() + self.nx * self.s_cell - self.s_cell, _col_cell.get(b.getName())[1].y() + self.ny * self.s_cell - self.s_cell)

        dx = new_cell.x() - old_cell.x()
        dy = new_cell.y() - old_cell.y()

        # De l'intervalle [old;new] on obitent old et new 
        old = QPainterPath()
        old.addRect(QRectF(old_cell.x() - 4, old_cell.y() - 4, w, h))
        new = QPainterPath()
        new.addRect(QRectF(new_cell.x() - 4, new_cell.y() - 4, w, h))

        # De l'intervalle [old;new] on determine ]old;new[
        intersection = QPainterPath()
        if dx != 0:
            intersection.moveTo(old_cell.x(), old_cell.y())
            intersection.lineTo(old_cell.x() + w, old_cell.y())
            intersection.lineTo(new_cell.x() + w, new_cell.y())
            intersection.lineTo(new_cell.x(), new_cell.y())
            intersection.closeSubpath()

            intersection.moveTo(old_cell.x(), old_cell.y() + h)
            intersection.lineTo(old_cell.x() + w, old_cell.y() + h)
            intersection.lineTo(new_cell.x() + w, new_cell.y() + h)
            intersection.lineTo(new_cell.x(), new_cell.y() + h)
            intersection.closeSubpath()

        if dy != 0:
            intersection.moveTo(old_cell.x(), old_cell.y())
            intersection.lineTo(old_cell.x(), old_cell.y() + h)
            intersection.lineTo(new_cell.x(), new_cell.y() + h)
            intersection.lineTo(new_cell.x(), new_cell.y())
            intersection.closeSubpath()

            intersection.moveTo(old_cell.x() + w, old_cell.y())
            intersection.lineTo(old_cell.x() + w, old_cell.y() + h)
            intersection.lineTo(new_cell.x() + w, new_cell.y() + h)
            intersection.lineTo(new_cell.x() + w, new_cell.y())
            intersection.closeSubpath()

        return old.united(new).united(intersection)

    
        
# little_Square
class Interface_Cell(QGraphicsRectItem):

    def __init__(self, x : int, y : int, w : int, h : int , backcell : bool):
        super().__init__(x, y, w, h)
        self._backcell = backcell
        if backcell == True : 
            self.setZValue(1)
        else :
            self.setZValue(3)
        self.w = w
        self.h = h
        self._coord = (None,None)
        self._img = None


    def paint(self, painter, option,/, widget = ...):
        global _background_set, _capturestart
        if self._backcell == False: 
            self.setBrush(QBrush(QColor("#686767ff")))
            
            if _capturestart == True:
                self.setPen(Qt.PenStyle.NoPen)
            else:    
                self.setPen(QPen(Qt.black, 0.5))
            tmp = self.parentItem()
            if _background_set == True : 
                self.setBrush(QBrush(QColor().fromString("transparent")))
            elif isinstance(tmp, IMG_SPACE):
                if tmp.isimg() == True :
                    self.setBrush(QBrush(QColor().fromString("transparent")))
        else:
            self.setPen(Qt.PenStyle.NoPen)
        
        return super().paint(painter, option, widget)

    def setImage(self, Path: str):
            global _background_set
            if self._backcell == True :
                if self._img is not None :
                    self.scene().removeItem(self._img)
                    del self._img

                self.Path = Path
                self._img = QGraphicsPixmapItem()
                self._img.setPixmap(QPixmap(Path))
                # utilise le cache au lieu de recharger depuis le disque
                scaled = _get_scaled_pixmap(Path, self.w, self.h)
                # Ne retirer de la scène que si l'item y est déjà (pixmap non null = déjà posé)
                if not self._img.pixmap().isNull() and self._img.scene() is not None:
                    self._img.scene().removeItem(self._img)
                self._img.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                self._img.setPixmap(scaled)
                w = self._img.pixmap().width() 
                h = self._img.pixmap().height()
                self._img.setPixmap(self._img.pixmap().copy(abs(self.w/2 - w/2),abs(self.h/2 - h/2),self.w,self.h))
                self._img.setPos(self.w * self._coord[0]  , self.h * self._coord[1])
                self._img.setParentItem(self)
                _background_set = True
                self.update()

    def removeimg(self) : 
        if self._img is not None :
            self.scene().removeItem(self._img)
            del self._img
            self._img = None
            


    def setName(self, i: str):
        self._name = i

    def getName(self):
        return self._name

    def getBackCell(self):
        return self._backcell


    def capture(self):
        global img, _filename_prefix,_destinate_folder
        self.update()
        if self._backcell == False :
            cap_zone = self.mapRectToScene(self.rect())
            img_ = QImage(cap_zone.size().toSize(),QImage.Format.Format_ARGB32)
            img_.fill(Qt.GlobalColor.transparent)
            paint = QPainter(img_)
            self.setVisible(False)
       #     self.parentItem().setVisible(False)
            if img is not None :
                img.setVisible(True)
            self.scene().render(paint, source=cap_zone)
       #     self.parentItem().setVisible(True)
            paint.end()
            self.setVisible(True)
            if not _filename_prefix or not _filename_prefix.strip() :    
                writer = QImageWriter(f"{_destinate_folder}/{time.strftime("%Y%m%d")}_{self._coord[0]}_{self._coord[1]}.png")
            else : 
                writer = QImageWriter(f"{_destinate_folder}/{_filename_prefix}_{self._coord[0]}_{self._coord[1]}.png")
            if writer.write(img_) == False :
                if writer.error().value == QImageWriter.ImageWriterError.DeviceError:
                    return False
            if img is not None :
                img.setVisible(True)
        self._capturestart = False
        return True

    def setCoord(self, x: int, y: int):
            self._coord = (x, y)
    

#where the image take place
class IMG(QGraphicsRectItem):
    def __init__(self, path :str, sizex :int, sizey :int, parent : IMG_SPACE):
        global _is_a_gif,_frame
        super().__init__(0, 0, sizex, sizey, parent)
        self._img = QGraphicsPixmapItem()
        if _is_a_gif == False :
            self._img.setPixmap(QPixmap(path).scaled(sizex,sizey))
        else:
            tmp = QMovie(path)
            tmp.jumpToFrame(0)
            for _ in range(1,_frame):
                tmp.jumpToNextFrame()
            self._img.setPixmap(tmp.currentPixmap().scaled(sizex,sizey))

        
        self._w=sizex
        self._h=sizey

        self.setZValue(2)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemContainsChildrenInShape)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable,True)
        self.setTransformOriginPoint(self.boundingRect().center())
        self._img.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self._img.setParentItem(self)

    def paint(self, painter, option, /, widget = ...):

        if self.isSelected() :
            option.state &= ~QStyle.State_Selected 
            self.setPen(QPen(Qt.red, 3, Qt.PenStyle.DashLine))
        else :
            self.setPen(QPen(Qt.transparent, 3, Qt.PenStyle.DashLine))

        return super().paint(painter, option, widget)

    def getsize(self):
        return (self._w,self._h)

    def getVisualW(self):
        return self._w

    def getVisualH(self):
        return self._h
    
    def rotation_update(self):
        tmp = self._w
        self._w = self._h
        self._h = tmp

class DesignSquare(QLabel):
    
    def __init__(self, parent_view : View_Interface_divise,W:int,H:int):
        super().__init__(parent_view)
        self.W=W
        self.H=H
        self.setFixedSize(W,H)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,True)
        
        self.setStyleSheet(
            "background-color: #222222 ;"
            "color: #ffffff;"
            "font-size: 12px;"
            "border-radius: 10px;")
        
        self._reposition()

    def _reposition(self):
        parent = self.parent()
        if parent is not None: 
            self.move((parent.width()-self.W)-10,52)

    def Align(self):
            self._reposition()   

class Space_Positions(QLabel):

    W = 98
    H = 81
    
    def __init__(self, parent_view : View_Interface_divise, scene : QGraphicsScene):
        super().__init__(parent_view)
        
        self.setFixedSize(self.W, self.H)
        
        self.scene = scene
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)
        
        self.setStyleSheet(
            "background-color: transparent ;"
            "color: #ffffff;"
            "font-size: 12px;"
            "border-radius: 3px;")
        
        self._whospressed = ""
        
        self.raise_()
        self._reposition()
        self.square = {}
        self.square["TL"] = Square_positon(self,scene,"TL")
        self.square["TC"] = Square_positon(self,scene,"TC")
        self.square["TR"] = Square_positon(self,scene,"TR")
        self.square["CL"] = Square_positon(self,scene,"CL")
        self.square["CC"] = Square_positon(self,scene,"CC")
        self.square["CR"] = Square_positon(self,scene,"CR")
        self.square["BL"] = Square_positon(self,scene,"BL")
        self.square["BC"] = Square_positon(self,scene,"BC")
        self.square["BR"] = Square_positon(self,scene,"BR")

    def _reposition(self):
        parent = self.parent()
        if parent is not None: 
            self.move((parent.width()-self.W)-20,self.H-15)


    def Align(self):
        self._reposition()   
        for sq in self.square :
            sq.Align()     

    def whospress(self):
        return self._whospressed

    def setwhospress(self,name : str):
        if self._whospressed != name :
            if self._whospressed != "" :
                self.square[self._whospressed].unpress()
            self._whospressed = name
            self.square[self._whospressed].press()

    def unpress(self):
        if self._whospressed != "" :
            self.square[self._whospressed].unpress()
        

class Square_positon(QLabel):

    W = 30
    H = 25
    round = 4
    
    
    def __init__(self, parent_view : Space_Positions, scene : QGraphicsScene, name : str):
        super().__init__(parent_view)
        
        self.setFixedSize(self.W, self.H)
        self._name = name
        self.scene = scene
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)

        self.setStyleSheet("""
            QLabel{
                background-color: #1A1A1A;
                color: #ffffff;
                font-size: 12px;
                border-radius: 3px;
            }
            QLabel:hover{
                background-color: #4E4E4E;
            }

            """)

        self._pressval = False            

        self.raise_()
        self._reposition()

    def _reposition(self):
        parent = self.parent()
        if parent is not None:
            if self._name == "TL":
                self.move((parent.width())-96,2)
            elif self._name == "TC":
                self.move((parent.width())-64,2)     
            elif self._name == "TR":
                self.move((parent.width())-32,2)
            elif self._name == "CL":
                self.move((parent.width())-96,self.H+3)
            elif self._name == "CC":
                self.move((parent.width())-64,self.H+3)
            elif self._name == "CR":
               self.move((parent.width())-32,self.H+3)
            elif self._name == "BL":
                self.move((parent.width())-96,self.H*2+4)
            elif self._name == "BC":
                self.move((parent.width())-64,self.H*2+4)
            elif self._name == "BR":
               self.move((parent.width())-32,self.H*2+4)
            else :
                self.move((parent.width()),self.H-30)


    def Align(self):
        self._reposition()        

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent().setwhospress(self._name)
            global img, _verticle
            if img is not None :
                img.setSelected(False)                        
                img_w = img.getsize()[0]
                img_h = img.getsize()[1]
                w = img.parentItem().getsize()[0]
                h = img.parentItem().getsize()[1]

                #Determine les valeurs de compensation pour positionner l'image lorsqu'il est à la vertical
                if _verticle == True : 

                    angle = math.radians(90)
                    
                    comp_w = (img_w - (abs(img_w * math.cos(angle)) + abs(img_h * math.sin(angle))))/2
                    comp_h = (img_h - (abs(img_w * math.sin(angle)) + abs(img_h * math.cos(angle))))/2


                if self._name == "TL":
                    if _verticle == False:
                        img.setPos(0,0)
                    else :
                        img.setPos(0-comp_w,0-comp_h)
                elif self._name == "TC":
                    if _verticle == False:
                        img.setPos(w/2-img_w/2,0)
                    else :
                        img.setPos((w/2-img_h/2)-comp_w,0-comp_h)
                elif self._name == "TR":
                    if _verticle == False:
                        img.setPos(w-img_w,0)
                    else:
                        img.setPos(w-img_h-comp_w,0-comp_h)
                elif self._name == "CL":
                    if _verticle == False:
                        img.setPos(0,h/2-img_h/2)
                    else:
                        img.setPos(0-comp_w,h/2-img_w/2-comp_h)
                elif self._name == "CC":
                    if _verticle == False:
                        img.setPos(w/2-img_w/2,h/2-img_h/2)
                    else:
                        img.setPos(w/2-img_h/2-comp_w,h/2-img_w/2-comp_h)
                elif self._name == "CR":
                    if _verticle ==False :
                        img.setPos(w-img_w,h/2-img_h/2)
                    else:
                        img.setPos(w-img_h-comp_w,h/2-img_w/2-comp_h)
                elif self._name == "BL":
                    if _verticle == False:
                        img.setPos(0,h-img_h)
                    else:
                        img.setPos(0-comp_w,h-img_w-comp_h)
                elif self._name == "BC":
                    if _verticle == False:
                        img.setPos(w/2-img_w/2,h-img_h)
                    else:
                        img.setPos(w/2-img_h/2-comp_w,h-img_w-comp_h)
                elif self._name == "BR":
                    if _verticle == False:
                        img.setPos(w-img_w,h-img_h)
                    else:
                        img.setPos(w-img_h-comp_w,h-img_w-comp_h)
            return super().mousePressEvent(event)

    def unpress(self):
        self._pressval = False
        self.setStyleSheet("""
            QLabel{
                background-color: #1A1A1A;
                color: #ffffff;
                font-size: 12px;
                border-radius: 3px;
            }
            QLabel:hover{
                background-color: #4E4E4E;
            }

            """)     

    def press(self):
        if self._pressval == False :
            self.setStyleSheet("background-color: #4E4E4E;")
            self._pressval = True

    

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)  
        

        space = self.rect().toRectF()

        draw = QPainterPath()

        draw.moveTo(space.center().x()-8,space.bottom()-2-self.round)        
        draw.lineTo(space.center().x()-8,space.top()+2 + self.round)       
        draw.quadTo(space.center().x()-8,space.top()+2,space.center().x()-8+self.round,space.top()+2)
        draw.lineTo(space.center().x()+8-self.round,space.top()+2)             
        draw.quadTo(space.center().x()+8,space.top()+2,space.center().x()+8,space.top()+2+self.round)
        draw.lineTo(space.center().x()+8,space.bottom()-2-self.round)
        draw.quadTo(space.center().x()+8,space.bottom()-2,space.center().x()+8-self.round,space.bottom()-2)
        draw.lineTo(space.center().x()-8+self.round,space.bottom()-2)
        draw.quadTo(space.center().x()-8,space.bottom()-2,space.center().x()-8,space.bottom()-2-self.round)
        #draw.lineTo(space.center().x()-8,space.bottom()-2-self.round)
        #draw.lineTo(space.right()/2,space.bottom()/1.9-8)

        draw.closeSubpath()

        outline  = QPainterPathStroker()
        outline.setWidth(1.5)
        
        
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#eff0ef")))
        painter.drawPath(outline.createStroke(draw))

        draw.clear()
        if self._name == "TL":
                    
            draw.moveTo(space.center().x()-7.5,space.center().y()+5-(self.round-1))        
            draw.lineTo(space.center().x()-7.5,space.top()+2.5 + (self.round-1))       
            draw.quadTo(space.center().x()-7.5,space.top()+2.5,space.center().x()-7.5+(self.round-1),space.top()+2.5)
            draw.lineTo(space.center().x()+3-(self.round-1),space.top()+2.5)             
            draw.quadTo(space.center().x()+3,space.top()+2.5,space.center().x()+3,space.top()+2.5+(self.round-1))
            draw.lineTo(space.center().x()+3,space.center().y()+2-(self.round-1))
            draw.quadTo(space.center().x()+3,space.center().y()+2,space.center().x()+3-(self.round-1),space.center().y()+2)
            draw.lineTo(space.center().x()-7.5+(self.round-1),space.center().y()+2)
            draw.quadTo(space.center().x()-7.5,space.center().y()+2,space.center().x()-7.5,space.center().y()+2-(self.round-1))
            
        elif self._name == "TC":

            draw.moveTo(space.center().x()-5,space.center().y()+5-(self.round-1))        
            draw.lineTo(space.center().x()-5,space.top()+2.5 + (self.round-1))       
            draw.quadTo(space.center().x()-5,space.top()+2.5,space.center().x()-5+(self.round-1),space.top()+2.5)
            draw.lineTo(space.center().x()+5-(self.round-1),space.top()+2.5)             
            draw.quadTo(space.center().x()+5,space.top()+2.5,space.center().x()+5,space.top()+2.5+(self.round-1))
            draw.lineTo(space.center().x()+5,space.center().y()+2-(self.round-1))
            draw.quadTo(space.center().x()+5,space.center().y()+2,space.center().x()+5-(self.round-1),space.center().y()+2)
            draw.lineTo(space.center().x()-5+(self.round-1),space.center().y()+2)
            draw.quadTo(space.center().x()-5,space.center().y()+2,space.center().x()-5,space.center().y()+2-(self.round-1))

        elif self._name == "TR":

            draw.moveTo(space.center().x()-3,space.center().y()+5-(self.round-1))        
            draw.lineTo(space.center().x()-3,space.top()+2.5 + (self.round-1))       
            draw.quadTo(space.center().x()-3,space.top()+2.5,space.center().x()-3+(self.round-1),space.top()+2.5)
            draw.lineTo(space.center().x()+7.32-(self.round-1),space.top()+2.5)             
            draw.quadTo(space.center().x()+7.32,space.top()+2.5,space.center().x()+7.32,space.top()+2.5+(self.round-1))
            draw.lineTo(space.center().x()+7.32,space.center().y()+2-(self.round-1))
            draw.quadTo(space.center().x()+7.32,space.center().y()+2,space.center().x()+7.32-(self.round-1),space.center().y()+2)
            draw.lineTo(space.center().x()-3+(self.round-1),space.center().y()+2)
            draw.quadTo(space.center().x()-3,space.center().y()+2,space.center().x()-3,space.center().y()+2-(self.round-1))
        
        elif self._name == "CL":
            
            draw.moveTo(space.center().x()-7.5,space.center().y()-(self.round-1))        
            draw.lineTo(space.center().x()-7.5,space.center().y()-6.5 + (self.round-1))       
            draw.quadTo(space.center().x()-7.5,space.center().y()-6.5,space.center().x()-7.5+(self.round-1),space.center().y()-6.5)
            draw.lineTo(space.center().x()+3-(self.round-1),space.center().y()-6.5)             
            draw.quadTo(space.center().x()+3,space.center().y()-6.5,space.center().x()+3,space.center().y()-6.5+(self.round-1))
            draw.lineTo(space.center().x()+3,space.center().y()+6.5-(self.round-1))
            draw.quadTo(space.center().x()+3,space.center().y()+6.5,space.center().x()+3-(self.round-1),space.center().y()+6.5)
            draw.lineTo(space.center().x()-7.5+(self.round-1),space.center().y()+6.5)
            draw.quadTo(space.center().x()-7.5,space.center().y()+6.5,space.center().x()-7.5,space.center().y()+6.5-(self.round-1))

        elif self._name == "CC":
                    
            draw.moveTo(space.center().x()-5,space.center().y()-(self.round-1))        
            draw.lineTo(space.center().x()-5,space.center().y()-6.5 + (self.round-1))       
            draw.quadTo(space.center().x()-5,space.center().y()-6.5,space.center().x()-5+(self.round-1),space.center().y()-6.5)
            draw.lineTo(space.center().x()+5-(self.round-1),space.center().y()-6.5)             
            draw.quadTo(space.center().x()+5,space.center().y()-6.5,space.center().x()+5,space.center().y()-6.5+(self.round-1))
            draw.lineTo(space.center().x()+5,space.center().y()+6.5-(self.round-1))
            draw.quadTo(space.center().x()+5,space.center().y()+6.5,space.center().x()+5-(self.round-1),space.center().y()+6.5)
            draw.lineTo(space.center().x()-5+(self.round-1),space.center().y()+6.5)
            draw.quadTo(space.center().x()-5,space.center().y()+6.5,space.center().x()-5,space.center().y()+6.5-(self.round-1))

        elif self._name == "CR":
        
            draw.moveTo(space.center().x()-3,space.center().y()-(self.round-1))        
            draw.lineTo(space.center().x()-3,space.center().y()-6.5 + (self.round-1))       
            draw.quadTo(space.center().x()-3,space.center().y()-6.5,space.center().x()-3+(self.round-1),space.center().y()-6.5)
            draw.lineTo(space.center().x()+7.32-(self.round-1),space.center().y()-6.5)             
            draw.quadTo(space.center().x()+7.32,space.center().y()-6.5,space.center().x()+7.32,space.center().y()-6.5+(self.round-1))
            draw.lineTo(space.center().x()+7.32,space.center().y()+6.5-(self.round-1))
            draw.quadTo(space.center().x()+7.32,space.center().y()+6.5,space.center().x()+7.32-(self.round-1),space.center().y()+6.5)
            draw.lineTo(space.center().x()-3+(self.round-1),space.center().y()+6.5)
            draw.quadTo(space.center().x()-3,space.center().y()+6.5,space.center().x()-3,space.center().y()+6.5-(self.round-1))        

        elif self._name == "BR":
                
            draw.moveTo(space.center().x()-3,space.center().y()+5-(self.round-1))        
            draw.lineTo(space.center().x()-3,space.center().y()-2 + (self.round-1))       
            draw.quadTo(space.center().x()-3,space.center().y()-2,space.center().x()-3+(self.round-1),space.center().y()-2)
            draw.lineTo(space.center().x()+7.5-(self.round-1),space.center().y()-2)             
            draw.quadTo(space.center().x()+7.5,space.center().y()-2,space.center().x()+7.5,space.center().y()-2+(self.round-1))
            draw.lineTo(space.center().x()+7.5,space.center().y()+10-(self.round-1))
            draw.quadTo(space.center().x()+7.5,space.center().y()+10,space.center().x()+7.5-(self.round-1),space.center().y()+10)
            draw.lineTo(space.center().x()-3+(self.round-1),space.center().y()+10)
            draw.quadTo(space.center().x()-3,space.center().y()+10,space.center().x()-3,space.center().y()+10-(self.round-1))

        elif self._name == "BL":
                            
            draw.moveTo(space.center().x()-7.5,space.center().y()-(self.round-1))        
            draw.lineTo(space.center().x()-7.5,space.center().y()-2 + (self.round-1))       
            draw.quadTo(space.center().x()-7.5,space.center().y()-2,space.center().x()-7.5+(self.round-1),space.center().y()-2)
            draw.lineTo(space.center().x()+3-(self.round-1),space.center().y()-2)             
            draw.quadTo(space.center().x()+3,space.center().y()-2,space.center().x()+3,space.center().y()-2+(self.round-1))
            draw.lineTo(space.center().x()+3,space.center().y()+10-(self.round-1))
            draw.quadTo(space.center().x()+3,space.center().y()+10,space.center().x()+3-(self.round-1),space.center().y()+10)
            draw.lineTo(space.center().x()-7.5+(self.round-1),space.center().y()+10)
            draw.quadTo(space.center().x()-7.5,space.center().y()+10,space.center().x()-7.5,space.center().y()+6.5-(self.round-1))

        elif self._name == "BC":
        
            draw.moveTo(space.center().x()-5,space.center().y()+5-(self.round-1))        
            draw.lineTo(space.center().x()-5,space.center().y()-2+(self.round-1))       
            draw.quadTo(space.center().x()-5,space.center().y()-2,space.center().x()-5+(self.round-1),space.center().y()-2)
            draw.lineTo(space.center().x()+5-(self.round-1),space.center().y()-2)             
            draw.quadTo(space.center().x()+5,space.center().y()-2,space.center().x()+5,space.center().y()-2+(self.round-1))
            draw.lineTo(space.center().x()+5,space.center().y()+10-(self.round-1))
            draw.quadTo(space.center().x()+5,space.center().y()+10,space.center().x()+5-(self.round-1),space.center().y()+10)
            draw.lineTo(space.center().x()-5+(self.round-1),space.center().y()+10)
            draw.quadTo(space.center().x()-5,space.center().y()+10,space.center().x()-5,space.center().y()+10-(self.round-1))
        
        draw.closeSubpath() 
        painter.drawPath(draw)
        
        
        return super().paintEvent(event)

class rotate_button(QLabel):

    W = 25
    H = 25
    round = 10    

    def __init__(self,parent : View_Interface_divise, coworker : IMG | IMG_SPACE, orientation : bool):
        super().__init__(parent)

        self._coworker = coworker
        self._orient = orientation    
        self.setFixedSize(self.W,self.H)
        
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)

        self.setStyleSheet("""
            QLabel{
                background-color: #222222;
                color: #ffffff;
                font-size: 12px;
                border-radius: 3px;
            }
            """)
        self.raise_()
        self._reposition()

    def _reposition(self):
        parent = self.parent()
        if parent is not None: 
            if self._orient == False : 
                self.move((parent.width()-self.W)-100,self.H+125)
            else :
                self.move((parent.width()-self.W)-15,self.H+125)

    def Align(self):
            self._reposition() 

    def mousePressEvent(self, event):
        global _verticle
        if event.button() == Qt.MouseButton.LeftButton:
            if self._orient == False : 
                _verticle = not _verticle
                if isinstance(self._coworker,IMG):
                    if self._coworker.rotation() == -270 :
                        self._coworker.setRotation(0)
                    else:
                        self._coworker.setRotation(self._coworker.rotation()-90)
                elif isinstance(self._coworker,IMG_SPACE):
                    if self._coworker.getimg() is not None:
                        if self._coworker.rotation() == -180.0:
                            self._coworker.getimg().setRotation(0)
                        else:
                            self._coworker.getimg().setRotation(self._coworker.getimg().rotation()-180)
            else : 
                _verticle = not _verticle
                if isinstance(self._coworker,IMG):
                    if self._coworker.rotation() == 270.0:
                        self._coworker.setRotation(0)
                    else:
                        self._coworker.setRotation(self._coworker.rotation()+90)
                elif isinstance(self._coworker,IMG_SPACE):
                    if self._coworker.getimg() is not None:
                        if self._coworker.rotation() == 180.0:
                            self._coworker.getimg().setRotation(0)
                        else:
                            self._coworker.getimg().setRotation(self._coworker.getimg().rotation()+180)

        return super().mousePressEvent(event)

    
    def paintEvent(self, arg__1):
    
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)  

        space = self.rect().toRectF()

          
        
        draw = QPainterPath()

        if self._orient == False:

            draw.moveTo(space.center())
            draw.arcTo(space.x()+4,space.y()+4,space.width()-8,space.height()-8,-70,200)


            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#eff0ef")))
            painter.drawPath(draw)

            draw.clear()
            draw.moveTo(space.center())
            draw.arcTo(space.x()+6,space.y()+6,space.width()-12,space.height()-12,0,360)

            painter.setBrush(QBrush(QColor("#222222")))
            painter.drawPath(draw)


            draw.clear()
            draw.moveTo(0,0)
            draw.arcMoveTo(space.x()+4,space.y()+4,space.width()-8,space.height()-8,130)
            #print(draw.currentPosition())
            draw.lineTo(draw.currentPosition().x()+1.5,draw.currentPosition().y()-3.5)

            outline  = QPainterPathStroker()
            outline.setWidth(1.5)

            painter.setBrush(QBrush(QColor("#eff0ef")))
            painter.drawPath(outline.createStroke(draw))       


            draw.clear()
            draw.moveTo(0,0)
            draw.arcMoveTo(space.x()+4,space.y()+4,space.width()-8,space.height()-8,130)
            #print(draw.currentPosition())
            draw.lineTo(draw.currentPosition().x()+3,draw.currentPosition().y()+3.5)

            outline  = QPainterPathStroker()
            outline.setWidth(1.5)

            painter.setBrush(QBrush(QColor("#eff0ef")))
            painter.drawPath(outline.createStroke(draw))       
        else :

            draw.moveTo(space.center())
            draw.arcTo(space.x()+4,space.y()+4,space.width()-8,space.height()-8,-70-50,-200)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#eff0ef")))
            painter.drawPath(draw)

            draw.clear()
            draw.moveTo(space.center())
            draw.arcTo(space.x()+6,space.y()+6,space.width()-12,space.height()-12,0,360)

            painter.setBrush(QBrush(QColor("#222222")))
            painter.drawPath(draw)

            draw.clear()
            draw.moveTo(0,0)
            draw.arcMoveTo(space.x()+4,space.y()+4,space.width()-8,space.height()-8,-320)
            #print(draw.currentPosition())
            draw.lineTo(draw.currentPosition().x()-1.5,draw.currentPosition().y()-3.5)

            outline  = QPainterPathStroker()
            outline.setWidth(1.5)

            painter.setBrush(QBrush(QColor("#eff0ef")))
            painter.drawPath(outline.createStroke(draw))       

            draw.clear()
            draw.moveTo(0,0)
            draw.arcMoveTo(space.x()+4,space.y()+4,space.width()-8,space.height()-8,-320)
            #print(draw.currentPosition())
            draw.lineTo(draw.currentPosition().x()-3,draw.currentPosition().y()+3.5)

            outline  = QPainterPathStroker()
            outline.setWidth(1.5)

            painter.setBrush(QBrush(QColor("#eff0ef")))
            painter.drawPath(outline.createStroke(draw))       
                    

        
        return super().paintEvent(arg__1)

class TextBoxesNameFile(QLineEdit):
    W = 80
    H = 28
    posH = 195

    def __init__(self,parent : View_Interface_divise):
        super().__init__(parent)

        f = QFont()
        f.setBold(True)

        text = QLabel(parent)
        text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignJustify )
        text.setText("Filles Names :")
        text.setStyleSheet("font-size : 10px;")
        text.setFont(f)
        text.adjustSize()
        text.move((parent.width()-self.W)-23,self.posH-12)
        
        self.setFixedSize(self.W,self.H)
        self.setPlaceholderText("Prefix")
        self.adjustSize()
        
        self.raise_()
        self._reposition()

    def _reposition(self):
            parent = self.parent()
            if parent is not None: 
                self.move((parent.width()-self.W)-26,self.posH)
        
        
    def Align(self):
        self._reposition()

    def keyPressEvent(self, event : QKeyEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Escape :
            self.clearFocus()
            return True 
        
        if event.key() == Qt.Key.Key_Backslash or event.key() == Qt.Key.Key_Slash or event.key() == Qt.Key.Key_Colon or event.key() == Qt.Key.Key_Period or event.key() == Qt.Key.Key_Asterisk or event.key() == Qt.Key.Key_QuoteLeft or event.key() == Qt.Key.Key_QuoteDbl or event.key() == Qt.Key.Key_Question or event.key() == Qt.Key.Key_questiondown or event.key() == Qt.Key.Key_Bar or event.key() == Qt.Key.Key_Less or event.key() == Qt.Key.Key_Greater :
            return True
        if len(self.text()) >= 15 :
            if event.key() == Qt.Key.Key_Backspace or event.key() == Qt.Key.Key_Delete or event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                return super().keyPressEvent(event)
            else:
                return True
        
        return super().keyPressEvent(event)

    def focusOutEvent(self, e):
        global _filename_prefix
        _filename_prefix = self.text()        
        return super().focusOutEvent(e)
               

class capture_button(QLabel):

    W = 80
    H = 38
        
    def __init__(self, parent_view : View_Interface_divise, scene : QGraphicsScene, subject : IMG_SPACE):
        super().__init__(parent_view)
        
        self.setFixedSize(self.W, self.H)
        self._subject = subject 
        self._scene = scene
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)

        self.setStyleSheet("""
            QLabel{
                background-color: #1A1A1A;
                color: #ffffff;
                font-size: 12px;
                border-radius: 8px;
            }
            QLabel:hover{
                background-color: #4E4E4E;
            }
            """)
        f = QFont()
        f.setBold(True)
        self.setFont(f)
        self.raise_()
        self._reposition()
        self.setText("Dividing")
        

    def _reposition(self):
            parent = self.parent()
            if parent is not None: 
                self.move((parent.width()-self.W)-26,245)
    
    
    def Align(self):
        self._reposition()

    def mousePressEvent(self, event):
        self._subject.captures()
        return super().mousePressEvent(event)

       
class Bacground_button(QLabel):

    W = 80
    H = 38
        
    def __init__(self, parent_view : View_Interface_divise, scene : QGraphicsScene, coworker : IMG_SPACE):
        super().__init__(parent_view)
        
        self.setFixedSize(self.W, self.H)
        
        self._scene = scene
        self._coworker = coworker
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)

        self.setStyleSheet("""
            QLabel{
                background-color: #1A1A1A;
                color: #ffffff;
                font-size: 12px;
                border-radius: 8px;
            }
            QLabel:hover{
                background-color: #4E4E4E;
            }
                    """)
        
        f = QFont()
        f.setBold(True)
        self.setFont(f)
        self.raise_()
        self._reposition()
        self.setText("Bacground")
        
        

    def _reposition(self):
            parent = self.parent()
            if parent is not None: 
                self.move((parent.width()-self.W)-26,self.H+260)
    
    
    def Align(self):
        self._reposition()

    def mousePressEvent(self, event):
        global _is_a_pattern
        path = QFileDialog.getOpenFileName(options=QFileDialog.Option.ReadOnly,filter="Images (*.png *.jpg *.jpeg *.gif)",caption="Dungeons Kitchen")
        if path != ('',''):
            option = popup_options(path[0])
            waiter = QEventLoop()
            option.destroyed.connect(waiter.quit)
            waiter.exec()
            self._coworker.setimage(path[0],_is_a_pattern)
        return super().mousePressEvent(event)


class Reset_Bacground_button(QLabel):

    W = 80
    H = 38
        
    def __init__(self, parent_view : View_Interface_divise, scene : QGraphicsScene, coworker : IMG_SPACE):
        super().__init__(parent_view)
        
        self.setFixedSize(self.W, self.H)
        
        self._scene = scene
        self._coworker = coworker
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)

        self.setStyleSheet("""
            QLabel{
                background-color: #1A1A1A;
                color: #ffffff;
                font-size: 12px;
                border-radius: 8px;
            }
            QLabel:hover{
                background-color: #4E4E4E;
            }
                        """)
        f = QFont()
        f.setBold(True)
        self.setFont(f)
        self.raise_()
        self._reposition()
        self.setText("Reset")
        

    def _reposition(self):
            parent = self.parent()
            if parent is not None: 
                self.move((parent.width()-self.W)-26,self.H*2+262)
    
    
    def Align(self):
        self._reposition()

    def mousePressEvent(self, event):
        self._coworker.removeimage()
        return super().mousePressEvent(event)


class popup_options(QWidget):
    def __init__(self, path : str):
        super().__init__()
        self.setWindowTitle("Options")
        self.setFixedSize(250,100)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.move(QApplication.primaryScreen().geometry().center() - self.rect().center())

        self._imgrender = QLabel()
        self._imgrender.setPixmap(QPixmap(path))
        # utilise le cache au lieu de recharger depuis le disque
        scaled = _get_scaled_pixmap(path, 60, 60)
        self._imgrender.setPixmap(scaled)
        self._imgrender.setParent(self)
        self._imgrender.move(10,10)
        
        self._check = QCheckBox("Pattern ?",self)
        self._check.move(self.rect().right()-self._check.width()+15,self.rect().center().y()-20)

        self._ok_button =QPushButton("Ok",self)
        self._cancel_button =QPushButton("Cancel",self)

        self._ok_button.setFixedSize(90,20)
        self._ok_button.move(self.rect().right()-95,self.rect().bottom() - 27)
        
        self._cancel_button.setFixedSize(90,20)
        self._cancel_button.move(self.rect().left()+60,self.rect().bottom() - 27)

        self._ok_button.clicked.connect(self.ok_action)
        self._cancel_button.clicked.connect(self.cancel_action)
        
        self._ok_is_pressed = False

        self.show()

    def closeEvent(self, event):
        if self._ok_is_pressed == False :
            global _is_a_pattern
            _is_a_pattern = None
        del self

    def ok_action(self):
        global _is_a_pattern
        if self._check.checkState().value == 0:
            _is_a_pattern = False
        else : 
            _is_a_pattern = True
        self._ok_is_pressed = True
        self.close()

    def cancel_action(self):
        self._ok_is_pressed =False
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
            self.ok_action()
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel_action()
        elif event.key() == Qt.Key.Key_P:
            self._check.setChecked(not self._check.isChecked())
        return super().keyPressEvent(event)

class popup_resize(QWidget):
    _key_shift_press = False
    def __init__(self, path : str):
            super().__init__()
            global img_W,img_H, _is_a_gif

            self.setWindowTitle("Set")
            self.setFixedSize(350,350)
            self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.move(QApplication.primaryScreen().geometry().center() - self.rect().center())
                    
            img_wh = get_image_size(path)
            img_W = img_wh[0]
            img_H = img_wh[1]
            self.no_text = QLabel(self)
            self._imgrender = QLabel()

            if _is_a_gif == True:
                scaled = _get_scaled_movie(path,80,80)
                self._imgrender.setMovie(scaled)
                self._imgrender.movie().jumpToFrame(0)
                self._imgrender.movie().setCacheMode(QMovie.CacheMode.CacheAll)
                self._imgrender.movie().stop()

                fsl = frameselector(self,False,self._imgrender)
                fsl.move(15+80*1.3,100)

                fsr = frameselector(self,True,self._imgrender)
                fsr.move(30+80*1.3,100)

            else:        
                self._imgrender.setPixmap(QPixmap(path))
                # utilise le cache au lieu de recharger depuis le disque
                scaled = _get_scaled_pixmap(path,80,80)
                self._imgrender.setPixmap(scaled)
            self._imgrender.setParent(self)
            self._imgrender.move(10,10)


            self._info = QLabel(self)
            self._info.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignJustify)
            self._info.setText(f"{path}")
            self._info.adjustSize()
            i = 0
            j = 0
            s = path
            while(self._info.width()>250):
                if path[i] == '/' and (j > 10 and j<40):  
                    s =  s[:(i+1)] + "\n" + s[(i+1):]
                    self._info.setText(f"{s}")
                    self._info.adjustSize()
                    j=0
                i = i+1
                j = j+1
            self._info.setText(f"{s} \n\n{img_W} x {img_H} px")
            self._info.adjustSize()
            self._info.move(100 + 20,15)
             


            self._imgsize = QLabel(self)
            self._imgsize.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignJustify )
            self._imgsize.setText(f"{img_W} x {img_H} px\n{math.ceil(img_W/64)} x {math.ceil(img_H/64)} grid")
            self._imgsize.adjustSize()
            self._imgsize.move(self.rect().center()- self._imgsize.rect().center() + QPointF(0,40).toPoint() )


            self._percent = Scale_SpinBox(self,suffix="%",minimum=0,decimals=2, maximum= sys.float_info.max, imgsizeLabel= self._imgsize)
            self._percent.setValue(100.00)
            self._predvalue = 100
            self._percent.setFixedSize(118,30)
            self._percent.adjustSize()
            self._percent.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._percent.move(self.rect().center() - self._percent.rect().center())

            txt_scale = QLabel(self)
            txt_scale.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignJustify )
            txt_scale.setText("Scale :")
            txt_scale.adjustSize()
            txt_scale.move(self.rect().center()- txt_scale.rect().center() - QPointF(self._percent.rect().width()/1.5,0).toPoint())
            self._percent.textChanged.connect(self.update_textscale)

            self._expand = QCheckBox("Expand",self)
            self._expand.move(self.rect().right()-self._expand.width()+12,self.rect().center().y()-12)
            self._expand.setToolTip("Will expand the image as the size of the scale")
            


            self._ok_button =QPushButton("Ok",self)
            self._cancel_button =QPushButton("Cancel",self)
    
            self._ok_button.setFixedSize(90,20)
            self._ok_button.move(self.rect().right()-95,self.rect().bottom() - 27)
            
            self._cancel_button.setFixedSize(90,20)
            self._cancel_button.move(self.rect().left()+160,self.rect().bottom() - 27)
            
            self._ok_button.clicked.connect(self.ok_action)
            self._cancel_button.clicked.connect(self.cancel_action)

            self.show()
    

    def closeEvent(self, event):
        del self


    def ok_action(self):
        global _set_step_valid , img_W , img_H, _expand, _frame, _is_a_gif
        if (img_W * (self._predvalue/100))<20 and (img_H * (self._predvalue/100))<20:
            
            self.no_text.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignJustify )
            self.no_text.setText("Minimum size is 20x20px\nPlease scale up")
            self.no_text.setStyleSheet("color: #f90004;")
            self.no_text.adjustSize()
            self.no_text.move(self.rect().center().x()-self.no_text.width()/2,self.rect().bottom()-self.no_text.height()-0)
            self.no_text.raise_()
            self.no_text.show()
        else: 
            img_W =  img_W * (self._predvalue/100)
            img_H =  img_H * (self._predvalue/100)
            _set_step_valid = True
            if self._expand.checkState() == Qt.CheckState.Checked :
                _expand = True
            else : 
                _expand = False
            if _is_a_gif == True:
                _frame = self._imgrender.movie().currentFrameNumber()
            self.close()
    
    def cancel_action(self):
        global _set_step_valid
        _set_step_valid = False
        self.close()

    def updatePredValue(self):
        self._predvalue = self._percent.value()

    def getPredValue(self):
        return self._predvalue 

    def update_textscale(self):
        if not self._predvalue == self._percent.value() :
            if self._percent.value() > 500.00 :
                self._percent.setValue(500.00)
            elif self._percent.value() < 25 :
                self._percent.setValue(25)
            self.updatePredValue()
            p = self._percent.value()/100
            self._imgsize.setText(f"{round(img_W*p,2)} x {round(img_H*p,2)} px\n{math.ceil((img_W*p)/64)} x {math.ceil((img_H*p)/64)} grid")
            self._imgsize.adjustSize()
            self._imgsize.move(self.rect().center()- self._imgsize.rect().center() + QPointF(0,40).toPoint())

    def mousePressEvent(self, event): 
        self.update_textscale()
        return super().mousePressEvent(event)

    def keyPressEvent(self, event  : QKeyEvent):

        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return :
            self.ok_action()
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_action()
        
        if event.key() == Qt.Key.Key_Shift:
            self._key_shift_press = True
        
        return super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Shift:
            self._key_shift_press = False
        return super().keyReleaseEvent(event)

    def get_shift_val(self):
        return self._key_shift_press

class Scale_SpinBox(QDoubleSpinBox):

    def __init__(self, parent : popup_resize,suffix : str ,minimum : float,decimals:int,maximum:float, imgsizeLabel : QLabel):
        super().__init__(parent=parent, suffix=suffix,minimum=minimum,decimals=decimals,maximum=maximum)
        self._imgsizeLabel = imgsizeLabel

    def keyPressEvent(self, event):
        global img_W , img_H
        if event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key.Key_Tab :
            if not self.parent().getPredValue() == self.value() : 
                if self.value() > 500.00 :
                    self.setValue(500.00)
                elif self.value() < 25 :
                    self.setValue(25)
                self.parent().updatePredValue()
                p = self.value()/100
                self._imgsizeLabel.setText(f"{round(img_W*p,2)} x {round(img_H*p,2)} px\n{math.ceil((img_W*p)/64)} x {math.ceil((img_H*p)/64)} grid")
                self._imgsizeLabel.adjustSize()
                self._imgsizeLabel.move(self.parent().rect().center()- self._imgsizeLabel.rect().center() + QPointF(0,40).toPoint() )
            self.clearFocus()
        return super().keyPressEvent(event)
    

class frameselector(QLabel):

    def __init__(self,parent:popup_resize, orient : bool, coworker:QLabel):
        super().__init__(parent=parent)
        self.orient=orient
        self.setFixedSize(12,12)
        self.setStyleSheet("""
            QLabel{
                background-color: #1A1A1A;
                color: #ffffff;
                font-size: 12px;
                border-radius: 2px;
            }
            QLabel:hover{
                background-color: #4E4E4E;
            }
        """)
        self.cowork = coworker
        

    def paintEvent(self, arg__1):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)  

        space = self.rect().toRectF()
        draw = QPainterPath()

        if self.orient == False:
            draw.moveTo(space.left()+1,space.center().y())
            draw.lineTo(space.center().x()+2.5,space.top()+1)
            draw.lineTo(space.center().x()+2.5,space.bottom()-1)
            draw.closeSubpath()
        else:
            draw.moveTo(space.right()-1,space.center().y())
            draw.lineTo(space.center().x()-2.5,space.top()+1)
            draw.lineTo(space.center().x()-2.5,space.bottom()-1)
            draw.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#eff0ef")))
        painter.drawPath(draw)


        return super().paintEvent(arg__1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.cowork.movie() is not None:
                m = self.cowork.movie()
                if self.orient == False :
                    if m.currentFrameNumber() != 0 :
                        if self.parent().get_shift_val() == False :
                            m.jumpToFrame((m.currentFrameNumber()-1))
                        else:
                            if m.currentFrameNumber()-10 < 0:
                                m.jumpToFrame(0)
                            else:
                                m.jumpToFrame(m.currentFrameNumber()-10)
                else:
                    if m.currentFrameNumber() != m.frameCount() :
                        if self.parent().get_shift_val() == False :
                            m.jumpToFrame(m.currentFrameNumber()+1)
                        else:
                            if m.currentFrameNumber()+10 > m.frameCount():
                                m.jumpToFrame(m.frameCount())
                            else:
                                m.jumpToFrame(m.currentFrameNumber()+10)
        return super().mousePressEvent(event)


# Opinion need here 7894
# CAN WE USE IT ? (I was thinking to check the size and if the size is too big or small refuse it)
# Adventage : Only reading de metadata of the image so optimised

#-------------------------------------------------------------------------------#
# Other source : https://github.com/scardine/image_size/blob/master/get_image_size.py
#-------------------------------------------------------------------------------#
# Source - https://stackoverflow.com/a/19035508
# Posted by Paulo Scardine, modified by community. See post 'Timeline' for change history
# Retrieved 2026-07-27, License - CC BY-SA 4.0

#-------------------------------------------------------------------------------
# Name:        get_image_size
# Purpose:     extract image dimensions given a file path using just
#              core modules
#
# Author:      Paulo Scardine (based on code from Emmanuel VAÏSSE)
#
# Created:     26/09/2013
# Copyright:   (c) Paulo Scardine 2013
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python


class UnknownImageFormat(Exception):
    pass

def get_image_size(file_path):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct modules from core
    """
    global _is_a_gif
    size = os.path.getsize(file_path)

    with open(file_path,mode="rb") as input:
        height = -1
        width = -1
        

        data = input.read(26)

        if (size >= 10) and data[:6] in (b'GIF87a', b'GIF89a'):
            # GIFs
            _is_a_gif = True
            w, h = struct.unpack("<HH", data[6:10])
            width = int(w)
            height = int(h)
        elif ((size >= 24) and data.startswith(b'\211PNG\r\n\032\n')
              and (data[12:16] == b'IHDR')):
            # PNGs  
            w, h = struct.unpack(">LL", data[16:24])
            width = int(w)
            height = int(h)
        elif (size >= 16) and data.startswith(b'\211PNG\r\n\032\n'):
            # older PNGs?
            w, h = struct.unpack(">LL", data[8:16])
            width = int(w)
            height = int(h)
        elif (size >= 2) and data.startswith(b'\377\330'):
            # JPEG
            msg = " raised while trying to decode as JPEG."
            input.seek(0)
            input.read(2)
            b = input.read(1)
            try:
                while (b and ord(b) != 0xDA):
                    while (ord(b) != 0xFF): b = input.read(1)
                    while (ord(b) == 0xFF): b = input.read(1)
                    if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                        input.read(3)
                        h, w = struct.unpack(">HH", input.read(4))
                        break
                    else:
                        input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                    b = input.read(1)
                width = int(w)
                height = int(h)
            except struct.error:
                raise UnknownImageFormat("StructError" + msg)
            except ValueError:
                raise UnknownImageFormat("ValueError" + msg)
            except Exception as e:
                raise UnknownImageFormat(e.__class__.__name__ + msg)
        else:
            raise UnknownImageFormat(
                "Sorry, don't know how to get information from this file."
            )

    return width, height

#-------------------------------------------------------------------------------#
#-------------------------------------------------------------------------------#

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = Divider_Window(64,"target_img","target_folder")
    window.show()
    sys.exit(app.exec())