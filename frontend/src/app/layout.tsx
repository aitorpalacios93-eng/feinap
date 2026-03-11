import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Audiovisual Jobs Premium",
  description: "Las mejores ofertas de empleo para el sector audiovisual",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body className={`${outfit.variable} antialiased min-h-screen bg-background text-foreground`}>
        {children}
      </body>
    </html>
  );
}
