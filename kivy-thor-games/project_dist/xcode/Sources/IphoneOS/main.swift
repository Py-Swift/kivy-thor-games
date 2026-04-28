import Foundation
import PySwiftKit
import Kivy3Launcher
import Kivy_iOS_Module

// 1 - post_imports
KivyLauncher.pyswiftImports = [
    .ios
]
// 3 - main
let exit_status = KivyLauncher.SDLmain()
// 5 - on_exit
exit(exit_status)