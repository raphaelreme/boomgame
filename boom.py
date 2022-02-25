"""Entry point for pyinstaller"""

from bomberman import main


if __name__ == "__main__":
    main.DEBUG = False
    main.main()
