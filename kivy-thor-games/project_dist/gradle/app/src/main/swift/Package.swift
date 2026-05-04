// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "KivyThorGames",
    products: [
        .library(name: "main", type: .dynamic, targets: ["main"]),
    ],
    dependencies: [
        .package(path: "../../../../../../../swift_packages/KivyLauncher")
    ],
    targets: [
        .target(
            name: "main",
            dependencies: [
                .product(name: "Kivy3Launcher", package: "KivyLauncher")
            ],
            path: "Sources/main",
            linkerSettings: [
                .linkedLibrary("log"),
            ]
        ),
    ]
)
