import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "../lib/query";
import { AuthProvider } from "../lib/auth";

export const metadata: Metadata = { title: "PayFlow — Accept Payments. Get Paid Faster.", description: "Secure payment platform for businesses of every size." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AuthProvider>{children}</AuthProvider>
        </Providers>
      </body>
    </html>
  );
}
