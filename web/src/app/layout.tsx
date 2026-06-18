import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'KiahBao.AI 🏡 仔包 — Singapore Housing Kaki',
  description:
    'Your friendly AI assistant for HDB grants, CPF usage, resale pricing, and renovation rules — powered by a local 27B SEA-LION model. No need to kiah lah!',
  keywords: ['HDB', 'CPF', 'Singapore housing', 'BTO', 'resale flat', 'EHG grant', 'KiahBao'],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
