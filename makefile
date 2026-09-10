# ===========================================================================
# Makefile – MJ Application (designer_pyside)
# Compatible Windows (cmd via GNU Make) et Linux/macOS
# Cibles : run | build-win | build-linux | clean
# Prérequis : python, pyinstaller  →  pip install pyinstaller
# ===========================================================================

# ── Détection de l'OS ───────────────────────────────────────────────────────
ifeq ($(OS), Windows_NT)
    DETECTED_OS := Windows
    SEP         := ;
    PYTHON      := py
    RM_DIR      := rmdir /s /q
    RM_FILE     := del /f /q
    MKDIR       := mkdir
else
    DETECTED_OS := Linux
    SEP         := :
    PYTHON      := python3
    RM_DIR      := rm -rf
    RM_FILE     := rm -f
    MKDIR       := mkdir -p
    CLEAN_PYC   := find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
                   find . -name "*.pyc" -delete 2>/dev/null; true
endif

# ── Répertoires ─────────────────────────────────────────────────────────────
DIST_DIR  := dist
BUILD_DIR := build
SPEC_DIR  := .

# ── Nom de l'exécutable ─────────────────────────────────────────────────────
APP_NAME     := MJ_Application
WIN_APP_NAME := DungeonKitchen
WIN_DIR_NAME := Dungeon Kitchen

# ── Chemins sources des données à embarquer ─────────────────────────────────
D_IMAGE    := ui/image
D_JSON     := json-styles
D_QSS      := Qss
D_SITE     := src/site
D_PHP      := src/MJ_application/php-portable
D_ASSETS   := Assets
D_PROJECTS := projects
D_LOCAL    := Local
ICON       := icon.png

# ── Options PyInstaller communes ────────────────────────────────────────────
PYINST_OPTS := \
	--noconfirm \
	--clean \
	--distpath "$(DIST_DIR)" \
	--workpath "$(BUILD_DIR)" \
	--specpath "$(SPEC_DIR)" \
	--add-data "$(D_IMAGE)$(SEP)image" \
	--add-data "$(D_JSON)$(SEP)json-styles" \
	--add-data "$(D_QSS)$(SEP)Qss" \
	--add-data "$(D_SITE)$(SEP)src/site" \
	--add-data "$(D_PHP)$(SEP)src/MJ_application/php-portable" \
	--add-data "$(D_ASSETS)$(SEP)Assets" \
	--add-data "$(D_PROJECTS)$(SEP)projects" \
	--add-data "$(ICON)$(SEP)." \
	--hidden-import Custom_Widgets \
	--hidden-import PySide6.QtSvg \
	--hidden-import PySide6.QtXml

# ---------------------------------------------------------------------------
.PHONY: help run build-win build-linux clean

help:
	@echo ""
	@echo "  OS detecte : $(DETECTED_OS)"
	@echo ""
	@echo "  Cibles disponibles :"
	@echo "    make run          - Lance l'application avec Python"
	@echo "    make build-win    - Compile un .exe Windows (--onedir)"
	@echo "    make build-linux  - Compile un binaire Linux  (--onedir)"
	@echo "    make clean        - Supprime build/, dist/ et les .spec"
	@echo ""

# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
run:
	$(PYTHON) main.py

# ---------------------------------------------------------------------------
# build-win
# ---------------------------------------------------------------------------
build-win:
	pyinstaller \
		$(PYINST_OPTS) \
		--name "$(WIN_APP_NAME)" \
		--windowed \
		--icon "ui/image/icon.png" \
		--onedir \
		--contents-directory "." \
		main.py
ifeq ($(DETECTED_OS), Windows)
	-$(RM_DIR) "$(DIST_DIR)\$(WIN_DIR_NAME)" 2>nul
	move /Y "$(DIST_DIR)\$(WIN_APP_NAME)" "$(DIST_DIR)\$(WIN_DIR_NAME)"
else
	-$(RM_DIR) "$(DIST_DIR)/$(WIN_DIR_NAME)"
	mv "$(DIST_DIR)/$(WIN_APP_NAME)" "$(DIST_DIR)/$(WIN_DIR_NAME)"
endif
	@echo ""
	@echo "  OK  Executable Windows : $(DIST_DIR)/$(WIN_DIR_NAME)/$(WIN_APP_NAME).exe"

# ---------------------------------------------------------------------------
# build-linux
# ---------------------------------------------------------------------------
build-linux:
	pyinstaller \
		$(PYINST_OPTS) \
		--name "$(APP_NAME)" \
		--onedir \
		main.py
	@echo ""
	@echo "  OK  Binaire Linux : $(DIST_DIR)/$(APP_NAME)"

# ---------------------------------------------------------------------------
# clean  –  fonctionne sur Windows (cmd) et Linux
# ---------------------------------------------------------------------------
clean:
ifeq ($(DETECTED_OS), Windows)
	-$(RM_DIR) $(BUILD_DIR) 2>nul
	-$(RM_DIR) $(DIST_DIR)  2>nul
	-$(RM_FILE) $(APP_NAME).spec 2>nul
	-$(RM_FILE) $(WIN_APP_NAME).spec 2>nul
	-for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
	-del /s /q *.pyc 2>nul
else
	$(RM_DIR) $(BUILD_DIR) $(DIST_DIR) $(APP_NAME).spec $(WIN_APP_NAME).spec
	$(CLEAN_PYC)
endif
	@echo "  OK  Nettoyage termine."