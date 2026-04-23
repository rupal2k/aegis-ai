"""NullMask isometric SVG illustrations — one constant per illustration."""

PRIVACY_VAULT = """<svg viewBox="0 0 400 440" xmlns="http://www.w3.org/2000/svg" fill="none">

    <!-- DOT CLOUD upper-left -->
    <g fill="#111">
      <circle cx="46" cy="206" r="1.8" opacity=".22"/><circle cx="60" cy="206" r="1.8" opacity=".30"/><circle cx="74" cy="206" r="1.8" opacity=".28"/><circle cx="88" cy="206" r="1.8" opacity=".20"/>
      <circle cx="46" cy="220" r="1.8" opacity=".30"/><circle cx="60" cy="220" r="1.8" opacity=".45"/><circle cx="74" cy="220" r="1.8" opacity=".48"/><circle cx="88" cy="220" r="1.8" opacity=".38"/><circle cx="102" cy="220" r="1.8" opacity=".20"/>
      <circle cx="46" cy="234" r="1.8" opacity=".28"/><circle cx="60" cy="234" r="1.8" opacity=".52"/><circle cx="74" cy="234" r="1.8" opacity=".60"/><circle cx="88" cy="234" r="1.8" opacity=".50"/><circle cx="102" cy="234" r="1.8" opacity=".28"/><circle cx="116" cy="234" r="1.8" opacity=".14"/>
      <circle cx="46" cy="248" r="1.8" opacity=".22"/><circle cx="60" cy="248" r="1.8" opacity=".50"/><circle cx="74" cy="248" r="1.8" opacity=".62"/><circle cx="88" cy="248" r="1.8" opacity=".54"/><circle cx="102" cy="248" r="1.8" opacity=".32"/><circle cx="116" cy="248" r="1.8" opacity=".16"/>
      <circle cx="60" cy="262" r="1.8" opacity=".40"/><circle cx="74" cy="262" r="1.8" opacity=".55"/><circle cx="88" cy="262" r="1.8" opacity=".50"/><circle cx="102" cy="262" r="1.8" opacity=".32"/><circle cx="116" cy="262" r="1.8" opacity=".18"/>
      <circle cx="60" cy="276" r="1.8" opacity=".28"/><circle cx="74" cy="276" r="1.8" opacity=".42"/><circle cx="88" cy="276" r="1.8" opacity=".38"/><circle cx="102" cy="276" r="1.8" opacity=".22"/>
      <circle cx="74" cy="290" r="1.8" opacity=".20"/><circle cx="88" cy="290" r="1.8" opacity=".26"/><circle cx="102" cy="290" r="1.8" opacity=".16"/>
    </g>

    <!-- CAMERA ORB LEFT -->
    <g>
      <line x1="80" y1="273" x2="105" y2="258" stroke="#111" stroke-width="2.2" stroke-linecap="round"/>
      <circle cx="80" cy="273" r="7" fill="#D8D8CE" stroke="#111" stroke-width="1.4"/>
      <circle cx="52" cy="273" r="27" fill="#EAEAE0" stroke="#111" stroke-width="1.5"/>
      <circle cx="52" cy="273" r="18" fill="#DCDCD4" stroke="#111" stroke-width="1.2"/>
      <circle cx="52" cy="273" r="11" fill="#D0D0C8" stroke="#111" stroke-width="1"/>
      <circle cx="52" cy="273" r="6.5" fill="#111"/>
      <circle cx="49" cy="270" r="2.2" fill="rgba(255,255,255,0.55)"/>
    </g>

    <!-- CAMERA ORB RIGHT -->
    <g>
      <line x1="320" y1="240" x2="295" y2="248" stroke="#111" stroke-width="2.2" stroke-linecap="round"/>
      <circle cx="320" cy="240" r="7" fill="#D8D8CE" stroke="#111" stroke-width="1.4"/>
      <circle cx="348" cy="240" r="27" fill="#EAEAE0" stroke="#111" stroke-width="1.5"/>
      <circle cx="348" cy="240" r="18" fill="#DCDCD4" stroke="#111" stroke-width="1.2"/>
      <circle cx="348" cy="240" r="11" fill="#D0D0C8" stroke="#111" stroke-width="1"/>
      <circle cx="348" cy="240" r="6.5" fill="#111"/>
      <circle cx="345" cy="237" r="2.2" fill="rgba(255,255,255,0.55)"/>
    </g>

    <!-- CHAMBER BODY sides (draw before top cap) -->
    <!-- Left angled face -->
    <polygon points="106,150 132,200 132,366 106,316" fill="rgba(0,0,0,0.045)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- Right angled face -->
    <polygon points="294,150 268,200 268,366 294,316" fill="rgba(0,0,0,0.065)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- Front glass face -->
    <polygon points="132,200 268,200 268,366 132,366" fill="rgba(210,210,195,0.14)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- Internal glow -->
    <ellipse cx="200" cy="288" rx="80" ry="48" fill="rgba(196,255,0,0.05)"/>

    <!-- Ghost blob inside -->
    <ellipse cx="200" cy="292" rx="50" ry="28" fill="rgba(0,0,0,0.04)"/>
    <ellipse cx="200" cy="292" rx="32" ry="17" fill="rgba(0,0,0,0.04)"/>

    <!-- ∅ LEFT (chartreuse) -->
    <circle cx="162" cy="284" r="37" stroke="#C4FF00" stroke-width="2.8" fill="rgba(196,255,0,0.06)"/>
    <line x1="135" y1="311" x2="189" y2="257" stroke="#C4FF00" stroke-width="2.8" stroke-linecap="round"/>

    <!-- ∅ RIGHT (chartreuse) -->
    <circle cx="240" cy="284" r="37" stroke="#C4FF00" stroke-width="2.8" fill="rgba(196,255,0,0.06)"/>
    <line x1="213" y1="311" x2="267" y2="257" stroke="#C4FF00" stroke-width="2.8" stroke-linecap="round"/>

    <!-- TOP CAP (octagon) -->
    <polygon points="132,100 200,76 268,100 294,150 268,200 200,224 132,200 106,150" fill="rgba(215,215,200,0.35)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- Cap inner dashed detail -->
    <polygon points="150,114 200,95 250,114 272,150 250,186 200,205 150,186 128,150" fill="none" stroke="rgba(0,0,0,0.10)" stroke-width="1" stroke-dasharray="3,5" stroke-linejoin="round"/>

    <!-- BASE dark slab -->
    <!-- Top surface of base -->
    <polygon points="70,366 330,366 358,392 42,392" fill="#1C1C1A" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- LED strips on top surface -->
    <rect x="88" y="371" width="46" height="9" rx="3" fill="#C4FF00" opacity=".9"/>
    <rect x="178" y="371" width="46" height="9" rx="3" fill="#C4FF00" opacity=".9"/>
    <rect x="268" y="371" width="46" height="9" rx="3" fill="#C4FF00" opacity=".9"/>
    <!-- Front face of base -->
    <polygon points="42,392 358,392 358,428 42,428" fill="#141412" stroke="#111" stroke-width="1.5"/>
    <!-- Recessed slots on front -->
    <rect x="86" y="397" width="48" height="14" rx="2.5" fill="#0C0C0A"/>
    <rect x="178" y="397" width="48" height="14" rx="2.5" fill="#0C0C0A"/>
    <rect x="265" y="397" width="48" height="14" rx="2.5" fill="#0C0C0A"/>
    <!-- Divider line -->
    <line x1="42" y1="408" x2="358" y2="408" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
    <!-- Bottom rail -->
    <rect x="56" y="426" width="290" height="8" rx="2" fill="#111"/>

    <!-- CABLE from box to base -->
    <path d="M 62,432 C 58,440 50,448 52,456 C 54,462 66,462 80,458 C 92,454 96,446 96,440" stroke="#111" stroke-width="2.2" stroke-linecap="round" fill="none"/>

    <!-- NULLMASK CONTROL BOX lower-left -->
    <!-- Top face (chartreuse) -->
    <polygon points="26,408 62,392 90,408 54,424" fill="#C4FF00" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- Left face (darker green) -->
    <polygon points="26,408 26,434 54,450 54,424" fill="#9BC800" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- Right face -->
    <polygon points="54,424 54,450 90,434 90,408" fill="#AADD00" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>
    <!-- ∅ on box top -->
    <circle cx="58" cy="408" r="9.5" stroke="#111" stroke-width="1.8" fill="rgba(0,0,0,0.10)"/>
    <line x1="51" y1="415" x2="65" y2="401" stroke="#111" stroke-width="1.8" stroke-linecap="round"/>

    <!-- Scatter dots -->
    <circle cx="330" cy="356" r="2.8" fill="#111" opacity=".45"/>
    <circle cx="344" cy="369" r="2.8" fill="#111" opacity=".45"/>
    <circle cx="356" cy="352" r="2" fill="#111" opacity=".28"/>
    <circle cx="362" cy="363" r="1.6" fill="#111" opacity=".20"/>

  </svg>"""

PRIVACY_ROUTER = """<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" fill="none">

    <!-- DOT CLOUD upper-right -->
    <g fill="#111">
      <circle cx="312" cy="58" r="1.8" opacity=".20"/><circle cx="326" cy="58" r="1.8" opacity=".28"/><circle cx="340" cy="58" r="1.8" opacity=".28"/><circle cx="354" cy="58" r="1.8" opacity=".20"/>
      <circle cx="298" cy="72" r="1.8" opacity=".18"/><circle cx="312" cy="72" r="1.8" opacity=".38"/><circle cx="326" cy="72" r="1.8" opacity=".48"/><circle cx="340" cy="72" r="1.8" opacity=".42"/><circle cx="354" cy="72" r="1.8" opacity=".25"/>
      <circle cx="312" cy="86" r="1.8" opacity=".30"/><circle cx="326" cy="86" r="1.8" opacity=".52"/><circle cx="340" cy="86" r="1.8" opacity=".55"/><circle cx="354" cy="86" r="1.8" opacity=".35"/>
      <circle cx="326" cy="100" r="1.8" opacity=".35"/><circle cx="340" cy="100" r="1.8" opacity=".42"/><circle cx="354" cy="100" r="1.8" opacity=".28"/>
      <circle cx="340" cy="114" r="1.8" opacity=".22"/><circle cx="354" cy="114" r="1.8" opacity=".18"/>
    </g>

    <!-- Incoming chain lines (left side) -->
    <g stroke="#111" stroke-width="1.4" stroke-linecap="round">
      <line x1="30" y1="160" x2="118" y2="194"/>
      <line x1="30" y1="195" x2="118" y2="214"/>
      <line x1="30" y1="228" x2="118" y2="232"/>
    </g>
    <!-- Incoming coin icons -->
    <g>
      <circle cx="22" cy="160" r="10" fill="#E8E8E0" stroke="#111" stroke-width="1.3"/>
      <text x="22" y="164" text-anchor="middle" font-size="8" fill="#111" font-family="monospace" font-weight="700">E</text>
      <circle cx="22" cy="195" r="10" fill="#E8E8E0" stroke="#111" stroke-width="1.3"/>
      <text x="22" y="199" text-anchor="middle" font-size="8" fill="#111" font-family="monospace" font-weight="700">A</text>
      <circle cx="22" cy="228" r="10" fill="#E8E8E0" stroke="#111" stroke-width="1.3"/>
      <text x="22" y="232" text-anchor="middle" font-size="8" fill="#111" font-family="monospace" font-weight="700">P</text>
    </g>

    <!-- Outgoing shielded lines (right side) -->
    <g stroke="#C4FF00" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="5,3">
      <line x1="282" y1="207" x2="370" y2="172"/>
      <line x1="282" y1="235" x2="370" y2="220"/>
      <line x1="282" y1="260" x2="370" y2="268"/>
    </g>
    <!-- Shielded output icons -->
    <g>
      <circle cx="378" cy="172" r="10" fill="rgba(196,255,0,0.14)" stroke="#9BC800" stroke-width="1.3"/>
      <text x="378" y="176" text-anchor="middle" font-size="9" fill="#5A7A00" font-family="monospace">∅</text>
      <circle cx="378" cy="220" r="10" fill="rgba(196,255,0,0.14)" stroke="#9BC800" stroke-width="1.3"/>
      <text x="378" y="224" text-anchor="middle" font-size="9" fill="#5A7A00" font-family="monospace">∅</text>
      <circle cx="378" cy="268" r="10" fill="rgba(196,255,0,0.14)" stroke="#9BC800" stroke-width="1.3"/>
      <text x="378" y="272" text-anchor="middle" font-size="9" fill="#5A7A00" font-family="monospace">∅</text>
    </g>

    <!-- ISOMETRIC BOX DEVICE -->
    <!-- Using iso math: origin (200,270), W=130, D=85, H=110 -->
    <!-- A=(200,270) B=(313,335) C=(239,378) D=(126,313) -->
    <!-- A'=(200,160) B'=(313,225) C'=(239,268) D'=(126,203) -->

    <!-- Back left face (D,A,A',D') - slightly visible -->
    <polygon points="126,313 200,270 200,160 126,203" fill="rgba(0,0,0,0.03)" stroke="#111" stroke-width="1.2" stroke-linejoin="round"/>

    <!-- Right face (B,C,C',B') -->
    <polygon points="313,335 239,378 239,268 313,225" fill="rgba(0,0,0,0.055)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- Front face (A,B,B',A') - main face -->
    <polygon points="200,270 313,335 313,225 200,160" fill="rgba(220,220,205,0.35)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- Front face accent panel (top strip) -->
    <!-- Isometric strip at z=90-110 on front face (A): parallelogram strip near top -->
    <!-- Points at z=90: (200,270-90)=(200,180) and (313,335-90)=(313,245) -->
    <!-- Points at z=110: (200,160) and (313,225) -->
    <polygon points="200,160 313,225 313,238 200,193" fill="#C4FF00" stroke="#111" stroke-width="1"/>

    <!-- Port slots on front face (z=20-50 area) -->
    <!-- Port at x=30-60, z=20-50: screen x≈200+30*0.866=226, y=270+30*0.5-20=265 to y=270+30*0.5-50=235 -->
    <!-- I'll just place them visually: -->
    <g>
      <!-- Port 1 -->
      <polygon points="218,278 240,291 240,270 218,257" fill="#0C0C0A" stroke="#111" stroke-width="1"/>
      <polygon points="218,257 240,270 246,266 224,253" fill="#1A1A18" stroke="#111" stroke-width="1"/>
      <!-- Chartreuse LED on port 1 -->
      <circle cx="229" cy="278" r="3" fill="#C4FF00"/>

      <!-- Port 2 -->
      <polygon points="248,295 270,308 270,287 248,274" fill="#0C0C0A" stroke="#111" stroke-width="1"/>
      <polygon points="248,274 270,287 276,283 254,270" fill="#1A1A18" stroke="#111" stroke-width="1"/>
      <circle cx="259" cy="295" r="3" fill="#C4FF00"/>

      <!-- Port 3 -->
      <polygon points="278,312 300,325 300,304 278,291" fill="#0C0C0A" stroke="#111" stroke-width="1"/>
      <polygon points="278,291 300,304 306,300 284,287" fill="#1A1A18" stroke="#111" stroke-width="1"/>
      <circle cx="289" cy="312" r="3" fill="#9BC800" opacity=".7"/>
    </g>

    <!-- NullMask branding on front (low) -->
    <!-- Small ∅ stamp on front face -->
    <circle cx="215" cy="320" r="12" stroke="#111" stroke-width="1.5" fill="rgba(0,0,0,0.06)"/>
    <line x1="207" y1="328" x2="223" y2="312" stroke="#111" stroke-width="1.5" stroke-linecap="round"/>
    <!-- "NULLMASK" micro text -->

    <!-- LEFT FACE (D,A,A',D') visible part - left slant -->
    <!-- Actually A,D,D',A' = (200,270)(126,313)(126,203)(200,160) -->
    <polygon points="200,270 126,313 126,203 200,160" fill="rgba(0,0,0,0.03)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- TOP FACE (A'B'C'D') -->
    <polygon points="200,160 313,225 239,268 126,203" fill="rgba(215,215,200,0.40)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- Top face routing diagram (stylized) -->
    <!-- Routing paths on top -->
    <g stroke="rgba(0,0,0,0.18)" stroke-width="1" fill="none">
      <path d="M 165,195 L 185,208 L 210,215 L 240,208 L 255,200"/>
      <path d="M 165,208 L 185,220 L 215,226 L 242,220"/>
    </g>
    <!-- Routing node dots on top -->
    <circle cx="185" cy="208" r="3" fill="#C4FF00" stroke="#111" stroke-width="0.8"/>
    <circle cx="215" cy="218" r="3" fill="#C4FF00" stroke="#111" stroke-width="0.8"/>
    <circle cx="242" cy="210" r="3" fill="#C4FF00" stroke="#111" stroke-width="0.8"/>

    <!-- Antenna on top-right corner -->
    <line x1="295" y1="225" x2="310" y2="168" stroke="#111" stroke-width="2" stroke-linecap="round"/>
    <circle cx="310" cy="165" r="5" fill="#E8E8E0" stroke="#111" stroke-width="1.5"/>
    <circle cx="310" cy="165" r="2.5" fill="#C4FF00"/>

    <!-- Small device on top-right of box top face -->
    <rect x="298" y="240" width="0" height="0"/>

    <!-- Base slab under device -->
    <polygon points="112,320 327,355 327,370 112,335" fill="#1C1C1A" stroke="#111" stroke-width="1.5"/>
    <!-- LED strip on base -->
    <rect x="0" y="0" width="0" height="0"/>
    <!-- Base front strip -->
    <polygon points="112,335 327,370 327,382 112,347" fill="#141412" stroke="#111" stroke-width="1.3"/>
    <!-- Chartreuse strip on base -->
    <polygon points="130,337 280,365 280,370 130,342" fill="#C4FF00" opacity=".85"/>

    <!-- Cable/plug bottom-left -->
    <path d="M 112,348 C 95,352 78,358 68,370 C 60,380 65,390 75,390" stroke="#111" stroke-width="2" stroke-linecap="round" fill="none"/>
    <rect x="62" y="387" width="26" height="14" rx="4" fill="#1C1C1A" stroke="#111" stroke-width="1.5"/>
    <rect x="68" y="393" width="14" height="5" rx="1.5" fill="#C4FF00"/>

    <!-- Scatter dots lower-left -->
    <circle cx="42" cy="320" r="2.5" fill="#111" opacity=".40"/>
    <circle cx="54" cy="334" r="2.5" fill="#111" opacity=".38"/>
    <circle cx="40" cy="338" r="1.8" fill="#111" opacity=".24"/>

  </svg>"""

PRIVACY_SHIELD = """<svg viewBox="0 0 400 420" xmlns="http://www.w3.org/2000/svg" fill="none">

    <!-- DOT CLOUD lower-right -->
    <g fill="#111">
      <circle cx="316" cy="320" r="1.8" opacity=".18"/><circle cx="330" cy="320" r="1.8" opacity=".26"/><circle cx="344" cy="320" r="1.8" opacity=".22"/>
      <circle cx="302" cy="334" r="1.8" opacity=".16"/><circle cx="316" cy="334" r="1.8" opacity=".36"/><circle cx="330" cy="334" r="1.8" opacity=".42"/><circle cx="344" cy="334" r="1.8" opacity=".30"/><circle cx="358" cy="334" r="1.8" opacity=".16"/>
      <circle cx="316" cy="348" r="1.8" opacity=".28"/><circle cx="330" cy="348" r="1.8" opacity=".48"/><circle cx="344" cy="348" r="1.8" opacity=".50"/><circle cx="358" cy="348" r="1.8" opacity=".32"/>
      <circle cx="330" cy="362" r="1.8" opacity=".32"/><circle cx="344" cy="362" r="1.8" opacity=".40"/><circle cx="358" cy="362" r="1.8" opacity=".28"/><circle cx="372" cy="362" r="1.8" opacity=".15"/>
      <circle cx="344" cy="376" r="1.8" opacity=".22"/><circle cx="358" cy="376" r="1.8" opacity=".28"/><circle cx="372" cy="376" r="1.8" opacity=".18"/>
      <circle cx="358" cy="390" r="1.8" opacity=".15"/><circle cx="372" cy="390" r="1.8" opacity=".12"/>
    </g>

    <!-- Outer glow ring (subtle) -->
    <ellipse cx="200" cy="200" rx="152" ry="188" stroke="rgba(196,255,0,0.12)" stroke-width="20" fill="none"/>

    <!-- SHIELD SHAPE (3D extruded isometric) -->

    <!-- Shield back face (left/shadow side, extruded) -->
    <path d="M 116,100 L 116,230 C 116,288 157,332 200,358 C 200,358 200,358 200,358 L 194,362 C 194,362 150,318 150,260 L 150,115 Z" fill="rgba(0,0,0,0.05)" stroke="rgba(0,0,0,0.0)"/>

    <!-- Shield left extrusion face -->
    <path d="
      M 84,82 L 84,215
      C 84,286 138,336 200,368
      L 200,358
      C 143,327 116,280 116,215
      L 116,100
      Z" fill="rgba(0,0,0,0.08)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- Shield top extrusion (thin top edge) -->
    <path d="M 84,82 L 316,82 L 284,70 L 52,70 Z" fill="rgba(220,220,205,0.50)" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/>

    <!-- Shield main front face -->
    <path d="
      M 116,100
      L 284,100
      L 284,228
      C 284,290 244,334 200,358
      C 156,334 116,290 116,228
      Z" fill="rgba(220,220,205,0.30)" stroke="#111" stroke-width="1.8" stroke-linejoin="round"/>

    <!-- Inner shield border -->
    <path d="
      M 140,118
      L 260,118
      L 260,224
      C 260,272 232,308 200,326
      C 168,308 140,272 140,224
      Z" fill="none" stroke="rgba(0,0,0,0.10)" stroke-width="1.2" stroke-dasharray="4,6" stroke-linejoin="round"/>

    <!-- Large ∅ symbol centered in shield -->
    <circle cx="200" cy="218" r="60" stroke="#C4FF00" stroke-width="3.5" fill="rgba(196,255,0,0.08)"/>
    <line x1="158" y1="260" x2="242" y2="176" stroke="#C4FF00" stroke-width="3.5" stroke-linecap="round"/>

    <!-- Shield top bar decorations -->
    <rect x="140" y="88" width="34" height="8" rx="3" fill="#C4FF00" stroke="#111" stroke-width="1"/>
    <rect x="226" y="88" width="34" height="8" rx="3" fill="#C4FF00" stroke="#111" stroke-width="1"/>
    <rect x="184" y="88" width="34" height="8" rx="3" fill="rgba(196,255,0,0.5)" stroke="#111" stroke-width="1"/>

    <!-- Corner rivets -->
    <circle cx="122" cy="107" r="5" fill="#D8D8CE" stroke="#111" stroke-width="1.2"/>
    <circle cx="278" cy="107" r="5" fill="#D8D8CE" stroke="#111" stroke-width="1.2"/>

    <!-- Status glyph bottom of shield -->
    <g transform="translate(200, 350)">
      <rect x="-24" y="-8" width="48" height="16" rx="8" fill="#C4FF00" stroke="#9BC800" stroke-width="1"/>
      <text x="0" y="5" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="8" fill="#111" font-weight="700" letter-spacing="0.5">PRIVATE</text>
    </g>

    <!-- Floating orbit ring -->
    <ellipse cx="200" cy="218" rx="88" ry="30" stroke="rgba(0,0,0,0.12)" stroke-width="1.2" stroke-dasharray="5,4" transform="rotate(-20 200 218)"/>

    <!-- Small floating modules -->
    <g>
      <!-- Left module -->
      <rect x="30" y="188" width="36" height="28" rx="5" fill="#EAEAE0" stroke="#111" stroke-width="1.3"/>
      <rect x="35" y="198" width="8" height="8" rx="2" fill="#C4FF00" stroke="#111" stroke-width="1"/>
      <rect x="48" y="198" width="12" height="3" rx="1" fill="rgba(0,0,0,0.12)"/>
      <rect x="48" y="204" width="8" height="3" rx="1" fill="rgba(0,0,0,0.08)"/>
      <line x1="66" y1="202" x2="84" y2="196" stroke="#111" stroke-width="1.2" stroke-dasharray="2,2"/>
    </g>
    <g>
      <!-- Right module -->
      <rect x="334" y="215" width="36" height="28" rx="5" fill="#EAEAE0" stroke="#111" stroke-width="1.3"/>
      <rect x="339" y="225" width="8" height="8" rx="2" fill="#C4FF00" stroke="#111" stroke-width="1"/>
      <rect x="352" y="225" width="12" height="3" rx="1" fill="rgba(0,0,0,0.12)"/>
      <rect x="352" y="231" width="8" height="3" rx="1" fill="rgba(0,0,0,0.08)"/>
      <line x1="334" y1="229" x2="316" y2="230" stroke="#111" stroke-width="1.2" stroke-dasharray="2,2"/>
    </g>

    <!-- NullMask mark bottom-left -->
    <g transform="translate(42, 380)">
      <rect x="0" y="0" width="28" height="28" rx="6" fill="#111"/>
      <circle cx="14" cy="14" r="7" stroke="#C4FF00" stroke-width="1.8"/>
      <line x1="8.5" y1="19.5" x2="19.5" y2="8.5" stroke="#C4FF00" stroke-width="1.8" stroke-linecap="round"/>
    </g>

  </svg>"""

ZERO_NODE = """<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" fill="none">

    <!-- DOT CLOUD upper-left -->
    <g fill="#111">
      <circle cx="40" cy="68" r="1.8" opacity=".18"/><circle cx="54" cy="68" r="1.8" opacity=".25"/><circle cx="68" cy="68" r="1.8" opacity=".22"/>
      <circle cx="40" cy="82" r="1.8" opacity=".25"/><circle cx="54" cy="82" r="1.8" opacity=".40"/><circle cx="68" cy="82" r="1.8" opacity=".44"/><circle cx="82" cy="82" r="1.8" opacity=".28"/>
      <circle cx="40" cy="96" r="1.8" opacity=".22"/><circle cx="54" cy="96" r="1.8" opacity=".44"/><circle cx="68" cy="96" r="1.8" opacity=".52"/><circle cx="82" cy="96" r="1.8" opacity=".40"/><circle cx="96" cy="96" r="1.8" opacity=".20"/>
      <circle cx="54" cy="110" r="1.8" opacity=".30"/><circle cx="68" cy="110" r="1.8" opacity=".44"/><circle cx="82" cy="110" r="1.8" opacity=".38"/><circle cx="96" cy="110" r="1.8" opacity=".22"/>
      <circle cx="68" cy="124" r="1.8" opacity=".28"/><circle cx="82" cy="124" r="1.8" opacity=".32"/><circle cx="96" cy="124" r="1.8" opacity=".18"/>
    </g>

    <!-- ORBITAL RINGS -->
    <!-- Outer horizontal ring (behind sphere) -->
    <ellipse cx="200" cy="200" rx="145" ry="40" stroke="rgba(0,0,0,0.10)" stroke-width="1.5" fill="none"/>
    <!-- Tilted ring 1 -->
    <ellipse cx="200" cy="200" rx="145" ry="40" stroke="rgba(0,0,0,0.08)" stroke-width="1.2" fill="none" transform="rotate(-35 200 200)"/>
    <!-- Tilted ring 2 -->
    <ellipse cx="200" cy="200" rx="145" ry="40" stroke="rgba(0,0,0,0.06)" stroke-width="1" fill="none" transform="rotate(35 200 200)"/>

    <!-- SPHERE (built from layers) -->
    <!-- Shadow underneath -->
    <ellipse cx="200" cy="328" rx="75" ry="14" fill="rgba(0,0,0,0.08)"/>

    <!-- Sphere back hemisphere (lighter) -->
    <circle cx="200" cy="195" r="110" fill="rgba(235,235,225,0.60)" stroke="#111" stroke-width="1.5"/>

    <!-- Sphere latitude lines (horizontal) -->
    <ellipse cx="200" cy="155" rx="100" ry="18" stroke="rgba(0,0,0,0.07)" stroke-width="1" fill="none"/>
    <ellipse cx="200" cy="195" rx="110" ry="22" stroke="rgba(0,0,0,0.07)" stroke-width="1" fill="none"/>
    <ellipse cx="200" cy="235" rx="100" ry="18" stroke="rgba(0,0,0,0.07)" stroke-width="1" fill="none"/>

    <!-- Sphere longitude lines (vertical) -->
    <ellipse cx="200" cy="195" rx="22" ry="110" stroke="rgba(0,0,0,0.07)" stroke-width="1" fill="none"/>
    <ellipse cx="200" cy="195" rx="70" ry="110" stroke="rgba(0,0,0,0.05)" stroke-width="1" fill="none"/>

    <!-- Sphere highlight (top-left sheen) -->
    <ellipse cx="168" cy="155" rx="42" ry="28" fill="rgba(255,255,255,0.35)"/>

    <!-- LARGE ∅ ON SPHERE FACE -->
    <circle cx="200" cy="195" r="72" stroke="#C4FF00" stroke-width="4" fill="rgba(196,255,0,0.07)"/>
    <line x1="149" y1="246" x2="251" y2="144" stroke="#C4FF00" stroke-width="4" stroke-linecap="round"/>

    <!-- Sphere outline -->
    <circle cx="200" cy="195" r="110" stroke="#111" stroke-width="1.8" fill="none"/>

    <!-- Connection ports (nodes on sphere surface) -->
    <!-- Top port -->
    <circle cx="200" cy="87" r="8" fill="#E8E8E0" stroke="#111" stroke-width="1.4"/>
    <circle cx="200" cy="87" r="4" fill="#C4FF00"/>
    <!-- Right port -->
    <circle cx="308" cy="195" r="8" fill="#E8E8E0" stroke="#111" stroke-width="1.4"/>
    <circle cx="308" cy="195" r="4" fill="#C4FF00"/>
    <!-- Left port -->
    <circle cx="92" cy="195" r="8" fill="#E8E8E0" stroke="#111" stroke-width="1.4"/>
    <circle cx="92" cy="195" r="4" fill="#9BC800"/>
    <!-- Bottom-right port -->
    <circle cx="278" cy="284" r="8" fill="#E8E8E0" stroke="#111" stroke-width="1.4"/>
    <circle cx="278" cy="284" r="4" fill="#9BC800" opacity=".7"/>

    <!-- Connecting cables from ports -->
    <line x1="200" y1="79" x2="200" y2="50" stroke="#111" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="200" cy="44" r="6" fill="#D8D8CE" stroke="#111" stroke-width="1.3"/>
    <circle cx="200" cy="44" r="2.5" fill="#111"/>

    <line x1="316" y1="195" x2="355" y2="195" stroke="#111" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="362" cy="195" r="7" fill="#D8D8CE" stroke="#111" stroke-width="1.3"/>
    <circle cx="362" cy="195" r="3" fill="#111"/>

    <line x1="84" y1="195" x2="45" y2="195" stroke="#111" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="38" cy="195" r="7" fill="#D8D8CE" stroke="#111" stroke-width="1.3"/>
    <circle cx="38" cy="195" r="3" fill="#C4FF00"/>

    <!-- Orbit particles (small dots on rings) -->
    <circle cx="316" cy="155" r="5" fill="#C4FF00" stroke="#111" stroke-width="1"/>
    <circle cx="84" cy="240" r="4" fill="#9BC800" stroke="#111" stroke-width="1"/>
    <circle cx="340" cy="228" r="3.5" fill="#C4FF00" stroke="#111" stroke-width="0.8"/>
    <circle cx="60" cy="162" r="3" fill="#111" opacity=".4"/>

    <!-- Small isometric platform base -->
    <polygon points="150,312 250,312 278,330 122,330" fill="#1C1C1A" stroke="#111" stroke-width="1.4"/>
    <polygon points="122,330 278,330 278,345 122,345" fill="#141412" stroke="#111" stroke-width="1.2"/>
    <!-- LED strip -->
    <rect x="148" y="333" width="50" height="6" rx="3" fill="#C4FF00" opacity=".9"/>
    <rect x="208" y="333" width="50" height="6" rx="3" fill="#C4FF00" opacity=".9"/>

    <!-- NullMask module lower-right -->
    <g transform="translate(314, 350)">
      <polygon points="0,0 28,-12 48,0 20,12" fill="#C4FF00" stroke="#111" stroke-width="1.4"/>
      <polygon points="0,0 0,18 20,30 20,12" fill="#9BC800" stroke="#111" stroke-width="1.4"/>
      <polygon points="20,12 20,30 48,18 48,0" fill="#AADD00" stroke="#111" stroke-width="1.4"/>
      <circle cx="24" cy="0" r="6.5" stroke="#111" stroke-width="1.5" fill="rgba(0,0,0,0.10)"/>
      <line x1="19.5" y1="5" x2="28.5" y2="-5" stroke="#111" stroke-width="1.5" stroke-linecap="round"/>
    </g>

    <!-- Cable from module to base -->
    <path d="M 314,362 C 300,358 295,350 278,342" stroke="#111" stroke-width="1.8" stroke-linecap="round" fill="none"/>

  </svg>"""
