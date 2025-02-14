"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { EyeIcon, EyeOffIcon } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    const res = await fetch("http://localhost:8000/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });

    setLoading(false);
    if (res.ok) {
      router.push("/dashboard");
      router.refresh();
    } else {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="relative flex items-center justify-center min-h-screen bg-gray-100">
      {/* Background Image */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-90"
        style={{ backgroundImage: "url('/bitsimage.jpg')" }}
      ></div>

      <div className="relative z-10 bg-white/40 backdrop-blur-md p-10 rounded-xl shadow-2xl max-w-md w-full text-center border border-white/30">
        <div className="font-extrabold text-4xl mb-4 text-gray-800 drop-shadow-lg">
          Admin Dashboard
        </div>
        <div className="font-semibold text-lg text-gray-700 mb-6">
          Welcome to BITS Admission Portal
        </div>

        <form onSubmit={handleLogin} className="w-full space-y-4">
          <h2 className="text-2xl font-bold mb-4 text-gray-900">Login</h2>
          <input
            type="email"
            placeholder="Email"
            className="p-3 border rounded-lg w-full focus:ring-2 focus:ring-blue-400 outline-none shadow-sm"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              className="p-3 border rounded-lg w-full focus:ring-2 focus:ring-blue-400 outline-none shadow-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-3 text-gray-500 hover:text-gray-700"
            >
              {showPassword ? <EyeOffIcon size={20} /> : <EyeIcon size={20} />}
            </button>
          </div>
          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-all shadow-md font-semibold disabled:bg-gray-400"
            disabled={loading}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
