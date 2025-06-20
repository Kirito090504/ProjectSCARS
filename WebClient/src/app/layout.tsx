// NOTE: react-scan must be the top-most import
import { ReactScan } from "@/components/dev/ReactScan";

import { Program } from "@/lib/info";
import { theme } from "@/lib/theme";
import { ColorSchemeScript, MantineProvider, mantineHtmlProps } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import type { Metadata } from "next";

import "@gfazioli/mantine-onboarding-tour/styles.css";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";
import "@mantine/spotlight/styles.css";

// Set page metadata
export const metadata: Metadata = {
    title: `${Program.name} | ${Program.description}`,
    description: Program.description,
};

interface RootLayoutProps {
    children: React.ReactNode;
}

/**
 * RootLayout component serves as the main layout for the application.
 * @param {RootLayoutProps} props - The properties for the RootLayout component.
 * @return {JSX.Element} The rendered RootLayout component.
 */
export default function RootLayout({ children }: RootLayoutProps) {
    console.debug("Rendering RootLayout");
    return (
        // Use mantineHtmlProps to handle the data-mantine-color-scheme attribute
        // and suppress hydration warnings for the <html> element.
        <html lang="en" {...mantineHtmlProps}>
            <head>
                <script
                    suppressHydrationWarning
                    dangerouslySetInnerHTML={{
                        // WARNING: This script contains hardcoded logic to determine the initial color scheme.
                        __html: `
                            (function() {
                                // Default to light mode if nothing is found or an error occurs
                                let initialColorScheme = 'light';
                                try {
                                    const stored = localStorage.getItem('user-preferences');
                                    if (stored) {
                                        const { darkMode } = JSON.parse(stored);
                                        initialColorScheme = darkMode ? 'dark' : 'light';
                                    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                                        // Fallback to system preference if no user preference is stored
                                        initialColorScheme = 'dark';
                                        localStorage.setItem('user-preferences', JSON.stringify({ darkMode: initialColorScheme === 'dark' }));
                                    }
                                    else {
                                        localStorage.setItem('user-preferences', JSON.stringify({ darkMode: false }));
                                    }
                                } catch (e) {
                                    console.error('Failed to read theme from localStorage:', e);
                                }

                                // Apply initial background/text color using Mantine color scheme variables
                                // This prevents a white flash before Mantine's CSS loads
                                document.documentElement.style.backgroundColor = initialColorScheme === 'dark' ? 'var(--mantine-color-dark)' : 'var(--mantine-color-light)';
                                document.documentElement.style.color = initialColorScheme === 'dark' ? 'var(--mantine-color-dark-text)' : 'var(--mantine-color-default-color)';
                                document.documentElement.setAttribute('data-mantine-color-scheme', initialColorScheme);
                            })();
                        `,
                    }}
                />
                <ColorSchemeScript />
            </head>
            <body>
                <ReactScan />
                <MantineProvider theme={theme} defaultColorScheme="auto">
                    {children}
                    <Notifications limit={5} autoClose={5000} />
                </MantineProvider>
            </body>
        </html>
    );
}
