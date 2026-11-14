// Logo de l'application : deux blocs reliés par une flèche (migration)
export default function Logo({ taille = 36 }) {
  return (
    <svg width={taille} height={taille} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <defs>
        <linearGradient id="logo-gradient" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#6366F1" />
          <stop offset="1" stopColor="#0EA5E9" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="10" fill="url(#logo-gradient)" />
      <rect x="8" y="22" width="11" height="9" rx="2" stroke="#fff" strokeWidth="2.2" />
      <rect x="21" y="9" width="11" height="9" rx="2" fill="#fff" />
      <path d="M13.5 19V15.5C13.5 14.4 14.4 13.5 15.5 13.5H18" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M16.5 11L19 13.5L16.5 16" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
