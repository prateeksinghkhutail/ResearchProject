"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    const res = await fetch("http://localhost:8000/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });

    if (res.ok) {
      router.push("/dashboard");
      router.refresh();
    } else {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="relative  flex items-center justify-center min-h-screen bg-gray-100">
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-80"
        style={{ backgroundImage: "url('/bitsimage.jpg')" }}
      ></div>

      <div className="relative z-10 bg-white p-8 rounded shadow-lg max-w-md w-full text-center">
        <div className="font-bold text-4xl mb-4 text-black">
          Admin Dashboard
        </div>
        <div className="font-bold text-xl text-gray-600 mb-6">
          Welcome to BITS Admission Dashboard
        </div>

        <form onSubmit={handleLogin} className="w-full">
          <h2 className="text-2xl font-bold mb-4">Login</h2>
          <input
            type="email"
            placeholder="Email"
            className="mb-3 p-2 border rounded w-full"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            className="mb-3 p-2 border rounded w-full"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
