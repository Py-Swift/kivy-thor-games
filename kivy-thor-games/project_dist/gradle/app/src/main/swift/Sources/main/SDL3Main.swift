// Android log levels: 3=DEBUG, 4=INFO, 5=WARN, 6=ERROR
@_silgen_name("__android_log_write")
@discardableResult
func androidLogWrite(_ prio: Int32, _ tag: UnsafePointer<CChar>?, _ text: UnsafePointer<CChar>?) -> Int32

// SDL_main entry point — called by SDLActivity
@_cdecl("SDL_main")
public func SDL_main(
    _ argc: Int32,
    _ argv: UnsafeMutablePointer<UnsafeMutablePointer<CChar>?>?
) -> Int32 {
    "Hello World from Swift!".withCString { msg in
        "SwiftMain".withCString { tag in
            androidLogWrite(4, tag, msg)
        }
    }
    return 0
}
