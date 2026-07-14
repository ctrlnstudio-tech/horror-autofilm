import AppKit

guard CommandLine.arguments.count >= 7,
      let width = Int(CommandLine.arguments[1]),
      let height = Int(CommandLine.arguments[2]) else {
    fputs("usage: thai_overlay width height output title subtitle vertical\n", stderr)
    exit(2)
}

let output = CommandLine.arguments[3]
let title = CommandLine.arguments[4]
let subtitle = CommandLine.arguments[5]
let vertical = CommandLine.arguments[6] == "1"

guard let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: width,
    pixelsHigh: height,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else {
    exit(3)
}

bitmap.size = NSSize(width: width, height: height)
guard let context = NSGraphicsContext(bitmapImageRep: bitmap) else { exit(4) }
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = context
NSColor.clear.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()

func paragraphStyle() -> NSMutableParagraphStyle {
    let style = NSMutableParagraphStyle()
    style.alignment = .center
    style.lineBreakMode = .byWordWrapping
    style.lineSpacing = 2
    return style
}

func textShadow(blur: CGFloat) -> NSShadow {
    let shadow = NSShadow()
    shadow.shadowColor = NSColor.black.withAlphaComponent(0.96)
    shadow.shadowBlurRadius = blur
    shadow.shadowOffset = NSSize(width: 0, height: -3)
    return shadow
}

let side = CGFloat(vertical ? 62 : 140)
let subtitleSize = CGFloat(vertical ? 42 : 34)
let subtitleFont = NSFont(name: "Thonburi", size: subtitleSize)
    ?? NSFont.systemFont(ofSize: subtitleSize, weight: .semibold)
let subtitleAttributes: [NSAttributedString.Key: Any] = [
    .font: subtitleFont,
    .foregroundColor: NSColor(calibratedRed: 1.0, green: 0.99, blue: 0.95, alpha: 1.0),
    .paragraphStyle: paragraphStyle(),
    .shadow: textShadow(blur: 8),
]
let attributedSubtitle = NSAttributedString(string: subtitle, attributes: subtitleAttributes)
let textWidth = CGFloat(width) - side * 2 - 40
let textBounds = attributedSubtitle.boundingRect(
    with: NSSize(width: textWidth, height: CGFloat(height) * 0.3),
    options: [.usesLineFragmentOrigin, .usesFontLeading]
)
let boxHeight = ceil(textBounds.height) + 32
let bottom = CGFloat(vertical ? 92 : 50)
let boxRect = NSRect(x: side, y: bottom, width: CGFloat(width) - side * 2, height: boxHeight)
let boxPath = NSBezierPath(roundedRect: boxRect, xRadius: 18, yRadius: 18)
NSColor.black.withAlphaComponent(0.31).setFill()
boxPath.fill()
let subtitleRect = NSRect(
    x: side + 20,
    y: bottom + 16,
    width: textWidth,
    height: ceil(textBounds.height) + 4
)
attributedSubtitle.draw(with: subtitleRect, options: [.usesLineFragmentOrigin, .usesFontLeading])

if !title.isEmpty {
    let titleSize = CGFloat(vertical ? 58 : 48)
    let titleFont = NSFont(name: "Thonburi-Bold", size: titleSize)
        ?? NSFont.boldSystemFont(ofSize: titleSize)
    let titleAttributes: [NSAttributedString.Key: Any] = [
        .font: titleFont,
        .foregroundColor: NSColor(calibratedRed: 0.965, green: 0.94, blue: 0.91, alpha: 1.0),
        .paragraphStyle: paragraphStyle(),
        .shadow: textShadow(blur: 10),
    ]
    let attributedTitle = NSAttributedString(string: title, attributes: titleAttributes)
    let titleSide = CGFloat(vertical ? 110 : 270)
    let titleWidth = CGFloat(width) - titleSide * 2
    let titleBounds = attributedTitle.boundingRect(
        with: NSSize(width: titleWidth, height: CGFloat(height) * 0.24),
        options: [.usesLineFragmentOrigin, .usesFontLeading]
    )
    let top = CGFloat(vertical ? 185 : 74)
    let titleRect = NSRect(
        x: titleSide,
        y: CGFloat(height) - top - ceil(titleBounds.height),
        width: titleWidth,
        height: ceil(titleBounds.height) + 6
    )
    attributedTitle.draw(with: titleRect, options: [.usesLineFragmentOrigin, .usesFontLeading])
}

context.flushGraphics()
NSGraphicsContext.restoreGraphicsState()
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(5) }
try png.write(to: URL(fileURLWithPath: output))
