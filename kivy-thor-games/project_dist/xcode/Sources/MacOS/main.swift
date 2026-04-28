import Foundation
import PySwiftKit
import Kivy3Launcher

// 1 - post_imports
KivyLauncher.pyswiftImports = [
    
]
// 3 - main
let exit_status = KivyLauncher.SDLmain()
// 5 - on_exit
exit(exit_status)