export default function FamilyIllustration() {
  return (
    <svg viewBox="44 34 342 216" role="presentation" focusable="false">
      <defs>
        <linearGradient id="care-paper" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#e9eadb" />
          <stop offset="1" stopColor="#d8e3d6" />
        </linearGradient>
        <linearGradient id="elder-skin" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#f0c8a9" />
          <stop offset="1" stopColor="#d9a987" />
        </linearGradient>
        <linearGradient id="caregiver-skin" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#c98f71" />
          <stop offset="1" stopColor="#aa715c" />
        </linearGradient>
        <linearGradient id="elder-coat" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#9caf9b" />
          <stop offset="1" stopColor="#6e8878" />
        </linearGradient>
        <linearGradient id="caregiver-coat" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stopColor="#d9a58b" />
          <stop offset="1" stopColor="#bd8068" />
        </linearGradient>
        <pattern id="cloth-grain" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(32)">
          <path d="M0 0v8" stroke="#f6eee0" strokeOpacity=".22" strokeWidth=".7" />
        </pattern>
        <filter id="care-figure-shadow" x="-15%" y="-15%" width="130%" height="135%">
          <feDropShadow dx="0" dy="3" stdDeviation="3" floodColor="#29423a" floodOpacity=".12" />
        </filter>
      </defs>

      <path d="M22 221c-7-44 10-93 42-132C99 46 145 22 198 27c47 4 73 31 116 38 41 7 76-5 97 22 20 26 11 76-3 134H22Z" fill="url(#care-paper)" />
      <path d="M56 223c-9-33 0-73 23-106 25-35 62-59 101-64m-101 26c25-25 55-39 87-42" fill="none" stroke="#b6c6b3" strokeOpacity=".62" strokeWidth="1.2" />
      <path d="M40 219c15-27 21-55 18-82m25 84c11-18 17-37 18-56m257 54c-8-27-7-50 3-72" fill="none" stroke="#8ba48d" strokeOpacity=".55" strokeWidth="1.2" strokeLinecap="round" />
      <path d="M35 192c14-20 27-29 43-31-5 16-18 27-43 31Zm26-34c7-21 17-33 32-39 1 17-9 31-32 39Zm300 27c-11-18-23-27-38-28 3 16 15 26 38 28Zm-10-37c-5-20-14-32-28-39-3 16 5 30 28 39Z" fill="#9bb09a" opacity=".8" />
      <path d="M27 229h376" fill="none" stroke="#b7c8b3" strokeWidth="1.2" />

      <g filter="url(#care-figure-shadow)">
        <path d="M61 249c3-37 15-70 44-88 17-11 38-15 58-12l39 9c30 7 48 39 52 91H61Z" fill="url(#elder-coat)" />
        <path d="M118 160c15 12 30 18 46 18 15 0 31-6 44-18l20 12-24 77h-79l-29-76 22-13Z" fill="#eee7d8" />
        <path d="M66 229c17-17 32-25 50-28m121 23c-12-15-23-22-39-26m-68-35 35 25 19-25" fill="none" stroke="#526f61" strokeOpacity=".68" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M129 186c10 6 22 10 35 10 12 0 25-4 35-10m-77 48c15-8 29-11 44-10m-39-24 8 24m66-24-9 24" fill="none" stroke="url(#cloth-grain)" strokeWidth="5" />

        <path d="M227 249c2-42 12-73 36-92 16-12 37-16 58-11 27 7 43 40 45 103H227Z" fill="url(#caregiver-coat)" />
        <path d="M265 151c12 11 24 16 36 16 12 0 24-5 35-16l17 12-21 86h-65l-22-84 20-14Z" fill="#f1e7d8" />
        <path d="M238 224c13-16 25-24 41-29m82 31c-12-14-24-22-39-26m-41-44 20 25 22-25" fill="none" stroke="#a96855" strokeOpacity=".7" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M272 184c9 5 18 8 29 8 10 0 20-3 29-8m-52 47c14-7 27-9 40-8m-34-24 7 24m48-24-7 24" fill="none" stroke="url(#cloth-grain)" strokeWidth="5" />

        <path d="M148 57c-17 3-28 17-28 36 0 22 14 42 34 48 15 5 32 0 42-12 7-8 9-17 8-27l9-8c3-3 0-6-5-8-2-19-17-33-36-34l-24 5Z" fill="url(#elder-skin)" />
        <path d="M121 84c-4-20 5-39 22-48 18-10 42-6 54 7 8 8 12 18 12 30-10-8-19-11-29-11-13 0-22 8-34 10-9 1-17 5-25 12Z" fill="#c6c7b9" />
        <path d="M125 71c7-17 20-27 37-30m-25 21c12-12 26-18 42-17m-23-7c14-2 26 3 35 13m-65 33c3-8 8-13 15-17m45-18c7 5 12 12 14 21" fill="none" stroke="#e2dfd0" strokeWidth="3" strokeLinecap="round" />
        <path d="M127 96c-8-3-13 1-12 8 1 7 6 11 14 10m79-28c7 0 11 5 9 11-1 5-5 8-11 8" fill="url(#elder-skin)" />
        <path d="M145 91c5-3 11-3 16 0m22-2c5-2 10-1 14 2" fill="none" stroke="#59635a" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M147 98c3-2 7-2 10 0m27-1c3-2 7-2 10 0" fill="none" stroke="#354d45" strokeWidth="2" strokeLinecap="round" />
        <path d="M170 96c-1 7-2 11-1 14 2 2 5 2 8 1m-19 10c6 4 13 5 20 1" fill="none" stroke="#a56759" strokeWidth="1.6" strokeLinecap="round" />
        <path d="M138 90c5-8 14-11 24-8l2 19c-10-1-18 1-25 6l-4-2 2-15Zm30-7c9-4 19-2 25 4l1 14c-8-4-16-5-26-2l-1-16Z" fill="none" stroke="#738578" strokeWidth="1.4" strokeLinejoin="round" />
        <path d="M164 92c2-2 4-3 7-3m-38 25c3 7 8 12 15 15m47-12c-3 6-7 10-13 13" fill="none" stroke="#c58f75" strokeWidth="1.2" strokeLinecap="round" />

        <path d="M294 52c17 2 28 18 26 38-1 20-14 40-32 47-14 5-29 0-39-11-7-8-10-17-9-27l-9-8c-3-3 0-6 5-8 1-18 16-32 34-34l24 3Z" fill="url(#caregiver-skin)" />
        <path d="M243 83c-3-19 4-37 20-47 15-9 38-9 52 0 12 8 18 20 17 36-9-7-19-9-29-8-13 1-20 9-32 12-9 2-19 3-28 7Z" fill="#354541" />
        <path d="M250 67c8-14 19-22 34-26m-22 17c12-10 25-14 40-13m-28-8c13-4 25-1 35 7m-74 42c4-8 10-12 17-14m48-24c8 5 13 12 16 20" fill="none" stroke="#65736b" strokeWidth="2.6" strokeLinecap="round" />
        <path d="M250 93c-7-2-12 2-11 8 1 6 5 10 12 10m75-23c7 1 10 6 8 12-2 5-6 8-12 8" fill="url(#caregiver-skin)" />
        <path d="M262 88c4-3 9-3 14-1m20 1c5-2 10-1 14 2" fill="none" stroke="#56483f" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M265 95c3-2 6-2 9 0m24 0c3-2 6-2 9 1" fill="none" stroke="#413d38" strokeWidth="2" strokeLinecap="round" />
        <path d="M285 94c1 6 2 10 1 13-2 2-5 2-8 1m-8 9c6 4 13 4 19 0" fill="none" stroke="#8e574b" strokeWidth="1.6" strokeLinecap="round" />
        <path d="M260 118c3 7 8 12 15 15m37-15c-3 6-7 10-13 13" fill="none" stroke="#b57961" strokeWidth="1.2" strokeLinecap="round" />

        <path d="M214 135c10-8 20-12 29-12 8 0 15 3 21 9" fill="none" stroke="#c6c7b9" strokeWidth="12" strokeLinecap="round" />
        <path d="M217 135c9-6 17-8 25-7 7 1 12 4 17 9" fill="none" stroke="#eee1cf" strokeWidth="8" strokeLinecap="round" />
        <path d="M122 180c17 14 35 20 55 18 14-1 26-7 37-17m35-3c-10 13-21 19-33 20-8 1-17-2-25-8" fill="none" stroke="#e2b596" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M196 193c6 6 12 8 18 7 5-1 9-4 13-8m-16 8c5 7 11 10 17 9 5-1 8-4 11-8m-24 2c5 7 10 10 15 9" fill="none" stroke="#d7a585" strokeWidth="2.2" strokeLinecap="round" />
      </g>

      <path d="M42 216c9-13 18-20 28-23m288 22c-9-15-18-22-29-25" fill="none" stroke="#829b84" strokeOpacity=".7" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M51 211c4-9 10-14 18-17m-9 19c5-8 11-12 18-13m272 11c-4-9-10-14-18-17m8 19c-5-8-11-12-18-13" fill="none" stroke="#a5b79e" strokeWidth="1" strokeLinecap="round" />
    </svg>
  );
}
