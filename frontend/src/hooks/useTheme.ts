import { useEffect, useState } from "react";
import type { Theme } from "@/types";

const STORAGE_KEY = "revtrace-theme";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // 1. Check localStorage
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (stored === "light" || stored === "dark") return stored;
    // 2. Fall back to OS preference
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return { theme, toggle, isDark: theme === "dark" };
}
