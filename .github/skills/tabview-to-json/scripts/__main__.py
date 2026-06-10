import sys

if sys.argv[1:] and sys.argv[1] == "view":
    from .csvseljson import main
else:
    from .extract import main

main()
