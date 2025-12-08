import React, { useState, useEffect } from "react";
import Chat from "./components/Chat";
import AuthModal from "./components/AuthModal";
import { AnimatePresence } from "framer-motion";

export default function App() {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("lawbot_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [showAuth, setShowAuth] = useState(false);

  const handleAuthSuccess = (userObj) => {
    localStorage.setItem("lawbot_user", JSON.stringify(userObj));
    setUser(userObj);
    setShowAuth(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("lawbot_user");
    setUser(null);
  };

  useEffect(() => {
    const onStorage = (e) => {
      if (e.key === "lawbot_user") {
        const raw = e.newValue;
        setUser(raw ? JSON.parse(raw) : null);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const displayName =
    user?.name ||
    (user?.email ? user.email.split("@")[0] : null) ||
    "Guest";

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-white via-[#f5f2fc] to-[#ebe4ff]">
      {/* Top section – slimmer, no shadow, no icon */}
      <header className="shrink-0 bg-gradient-to-r from-[#fef3ff] via-[#f5f2fc] to-[#e4f0ff] border-b border-white/60">
        {/* Navbar */}
        <nav className="max-w-6xl mx-auto px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl md:text-2xl font-bold tracking-tight">
              <span className="text-gray-900">Bharat</span>{" "}
              <span className="bg-gradient-to-r from-accent to-purple-500 bg-clip-text text-transparent">
                LawBot
              </span>
            </span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {user ? (
              <>
                <span className="hidden sm:inline text-gray-700">
                  Hi, {displayName}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1 rounded-full border border-accent text-accent hover:bg-accent hover:text-white transition"
                >
                  Logout
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowAuth(true)}
                className="px-3 py-1 rounded-full border border-accent text-accent hover:bg-accent hover:text-white transition text-sm"
              >
                Login / Signup / Guest
              </button>
            )}
          </div>
        </nav>

        {/* Hero text – compact, not “shadowing” main content */}
        <section className="max-w-6xl mx-auto px-4 pb-2 pt-1">
          <h1 className="text-lg md:text-2xl font-semibold text-gray-900 leading-snug max-w-3xl">
            A calm, friendly assistant for{" "}
            <span className="text-accent">Indian law</span>.
          </h1>
          <p className="mt-1 text-xs md:text-sm text-gray-600 max-w-2xl">
            Ask about sections, clauses, case law or contracts. Bharat LawBot
            uses Retrieval-Augmented Generation to explain things in simple
            English while keeping legal context intact.
          </p>
        </section>
      </header>

      {/* Main SPA content – fills remaining height, no page scroll; inner areas scroll */}
      <main className="flex-1 overflow-hidden flex justify-center px-2 md:px-4 py-3">
        <div className="w-full max-w-6xl h-full">
          <Chat user={user} />
        </div>
      </main>

      <footer className="shrink-0 py-2 text-center text-[11px] text-gray-500">
        © 2025 Bharat LawBot. All rights reserved.
      </footer>

      <AnimatePresence>
        {showAuth && (
          <AuthModal
            onSuccess={handleAuthSuccess}
            onClose={() => setShowAuth(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
