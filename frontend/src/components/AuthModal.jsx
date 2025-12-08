import React, { useState } from "react";
import { motion } from "framer-motion";
import axios from "axios";

const TABS = {
  LOGIN: "LOGIN",
  SIGNUP: "SIGNUP"
};

export default function AuthModal({ onSuccess, onClose }) {
  const [activeTab, setActiveTab] = useState(TABS.LOGIN);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const buildName = (override = {}) => {
    const rawEmail = override.email || email || "";
    const emailName =
      rawEmail && rawEmail.includes("@")
        ? rawEmail.split("@")[0]
        : undefined;
    return override.name || name || emailName || "Guest";
  };

  const baseUser = (override = {}) => ({
    id: override.id || `local-${Date.now()}`,
    name: buildName(override),
    email: override.email || email || "",
    isLocal: override.isLocal ?? true
  });

  const handleGuest = () => {
    onSuccess(baseUser({ name: "Guest", id: `guest-${Date.now()}` }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (activeTab === TABS.SIGNUP) {
        try {
          const res = await axios.post("/api/signup", { name, email, password });
          const apiUser = res.data?.user || {};
          const user = {
            id: apiUser.id || `local-${Date.now()}`,
            name: buildName({ name: apiUser.name, email: apiUser.email }),
            email: apiUser.email || email
          };
          onSuccess(user);
        } catch {
          onSuccess(baseUser());
        }
      } else {
        // LOGIN
        try {
          const res = await axios.post("/api/login", { email, password });
          const apiUser = res.data?.user || {};
          const user = {
            id: apiUser.id || `local-${Date.now()}`,
            name: buildName({ name: apiUser.name, email: apiUser.email || email }),
            email: apiUser.email || email
          };
          onSuccess(user);
        } catch {
          onSuccess(baseUser({ email }));
        }
      }
    } catch (err) {
      console.error(err);
      setError("Unable to authenticate. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="bg-white rounded-2xl shadow-soft w-full max-w-md p-6"
        initial={{ scale: 0.9, y: 20, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.9, y: 20, opacity: 0 }}
      >
        <h2 className="text-lg font-semibold text-center text-gray-900 mb-2">
          Welcome to <span className="text-accent">Bharat LawBot</span>
        </h2>
        <p className="text-xs text-gray-500 text-center mb-4">
          Log in, sign up, or continue as Guest. Your chats are stored
          securely in your browser, and can later be synced to backend.
        </p>

        {/* Tabs */}
        <div className="flex mb-4 rounded-full bg-softbg p-1 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab(TABS.LOGIN)}
            className={`flex-1 py-1.5 rounded-full ${
              activeTab === TABS.LOGIN
                ? "bg-white shadow-sm text-accent"
                : "text-gray-500"
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setActiveTab(TABS.SIGNUP)}
            className={`flex-1 py-1.5 rounded-full ${
              activeTab === TABS.SIGNUP
                ? "bg-white shadow-sm text-accent"
                : "text-gray-500"
            }`}
          >
            Signup
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3 text-sm">
          {activeTab === TABS.SIGNUP && (
            <input
              type="text"
              placeholder="Full name"
              className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          )}
          <input
            type="email"
            placeholder="Email"
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent/40"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <p className="text-xs text-red-500">{error}</p>}

          <button
            type="submit"
            disabled={busy}
            className="bg-accent text-white py-2 rounded-lg hover:opacity-90 disabled:opacity-60"
          >
            {busy
              ? "Please wait..."
              : activeTab === TABS.SIGNUP
              ? "Create account"
              : "Login"}
          </button>

          <button
            type="button"
            onClick={handleGuest}
            className="text-accent underline text-xs mt-1"
          >
            Continue as Guest
          </button>

          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 text-xs mt-2"
          >
            Cancel
          </button>
        </form>
      </motion.div>
    </motion.div>
  );
}
