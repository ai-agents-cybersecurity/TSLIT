#!/usr/bin/env python3
import os

def generate_logo():
    # Colors
    bg_color = "#0f172a"  # Slate 900
    primary_color = "#22d3ee"  # Cyan 400
    secondary_color = "#94a3b8"  # Slate 400
    accent_color = "#f472b6"  # Pink 400 (for glitch)

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="800" height="400">
    <!-- Background -->
    <rect width="800" height="400" fill="{bg_color}" rx="20" ry="20" />
    
    <!-- Grid Pattern Background -->
    <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="{secondary_color}" stroke-width="0.5" opacity="0.1"/>
        </pattern>
        <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:{primary_color};stop-opacity:1" />
            <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="800" height="400" fill="url(#grid)" rx="20" ry="20" />

    <!-- Main Text Group -->
    <g transform="translate(400, 200)" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold">
        
        <!-- Glitch Shadow Layer -->
        <text x="-4" y="4" font-size="120" fill="{accent_color}" opacity="0.3" letter-spacing="8">TSLIT</text>
        <text x="4" y="-4" font-size="120" fill="{primary_color}" opacity="0.3" letter-spacing="8">TSLIT</text>
        
        <!-- Main Text -->
        <text x="0" y="0" font-size="120" fill="url(#grad1)" letter-spacing="8" filter="url(#glow)">TSLIT</text>
        
        <!-- Subtitle -->
        <text x="0" y="60" font-size="24" fill="{secondary_color}" letter-spacing="4" font-weight="normal">TIME-SHIFT LLM INTEGRITY TESTER</text>
        
        <!-- Decorative Elements -->
        <!-- Top Line -->
        <path d="M -250 -80 L 250 -80" stroke="{primary_color}" stroke-width="2" opacity="0.5" />
        <rect x="-250" y="-83" width="10" height="6" fill="{primary_color}" />
        <rect x="240" y="-83" width="10" height="6" fill="{primary_color}" />
        
        <!-- Bottom Bracket -->
        <path d="M -200 90 L -220 90 L -220 70" stroke="{secondary_color}" stroke-width="2" fill="none" />
        <path d="M 200 90 L 220 90 L 220 70" stroke="{secondary_color}" stroke-width="2" fill="none" />
    </g>
</svg>'''

    output_path = "tslit_logo.svg"
    with open(output_path, "w") as f:
        f.write(svg_content)
    
    print(f"Successfully generated {output_path}")
    print("You can open this file in a web browser to view it.")

if __name__ == "__main__":
    generate_logo()
