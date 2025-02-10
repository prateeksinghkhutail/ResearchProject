"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Sidebar({ setActiveComponent }) {
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const router = useRouter();

  useEffect(() => {
    async function fetchUser() {
      const res = await fetch("http://localhost:8000/api/user", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      }
    }
    fetchUser();
  }, []);

  const handleLogout = async () => {
    await fetch("http://localhost:8000/api/logout", {
      method: "POST",
      credentials: "include",
    });
    router.push("/login");
  };

  return (
    <div className="fixed top-0 left-0 h-full w-64 bg-blue-800 text-white p-5 flex flex-col z-50">
      <div className="flex justify-center mb-6">
        <img
          src="/BITS_logo.png"
          alt="BITS Logo"
          className="w-20 h-20 rounded-full"
        />
      </div>

      <nav className="flex-1">
        <ul className="text-lg">
          <li>
            <button
              onClick={() => setActiveComponent("home")}
              className="block py-3 px-5 hover:bg-blue-700 w-full text-left"
            >
              Dashboard
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveComponent("students")}
              className="block py-3 px-5 hover:bg-blue-700 w-full text-left"
            >
              Student Details
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveComponent("iterations")}
              className="block py-3 px-5 hover:bg-blue-700 w-full text-left"
            >
              Iteration Details
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveComponent("fees")}
              className="block py-3 px-5 hover:bg-blue-700 w-full text-left"
            >
              Fee Details
            </button>
          </li>
        </ul>
      </nav>

      {user && (
        <div
          className="relative mt-auto p-4 cursor-pointer"
          onClick={() => setShowDropdown(!showDropdown)}
        >
          <div className="text-lg font-bold text-center">{user.name}</div>
          {showDropdown && (
            <div className="absolute left-4 bottom-12 w-48 bg-white text-black rounded shadow-lg">
              <button
                className="block w-full text-left px-4 py-2 hover:bg-gray-200"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
