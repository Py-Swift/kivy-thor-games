package org.example.kivythorgames;

import org.libsdl.app.SDLActivity;

public class MainActivity extends SDLActivity {

    @Override
    protected String[] getLibraries() {
        return new String[] {
            "SDL2",
            "python3",
            "main"
        };
    }
}