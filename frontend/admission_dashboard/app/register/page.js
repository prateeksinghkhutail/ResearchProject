"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [contact, setContact] = useState("");
  const [campus, setCampus] = useState("Pilani");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/api/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          name,
          email,
          contact,
          campus,
          password,
          confirmPassword,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        router.push("/login");
      } else {
        setError(data.detail || "Registration failed");
      }
    } catch (err) {
      setError("Failed to connect to the server");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="font-bold text-4xl my-4">Admin Registration</div>
      <div className="font-bold text-xl text-gray-500 my-2">
        Welcome to BITS Admission Dashboard
      </div>
      <form
        onSubmit={handleRegister}
        className="bg-white p-6 rounded shadow-md w-full max-w-lg"
      >
        <h2 className="text-2xl font-bold mb-4 text-center">Register</h2>
        {error && (
          <div className="mb-4 p-2 text-red-500 text-sm text-center">
            {error}
          </div>
        )}

        {/* Name Field */}
        <input
          type="text"
          placeholder="Full Name"
          className="mb-3 p-2 border rounded w-full"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        {/* Email Field */}
        <input
          type="email"
          placeholder="Email"
          className="mb-3 p-2 border rounded w-full"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        {/* Contact Field */}
        <input
          type="tel"
          pattern="[1-9]{1}[0-9]{9}"
          placeholder="Contact Number"
          className="mb-3 p-2 border rounded w-full"
          value={contact}
          onChange={(e) => setContact(e.target.value)}
          required
        />

        {/* Campus Dropdown */}
        <select
          className="mb-3 p-2 border rounded w-full bg-white"
          value={campus}
          onChange={(e) => setCampus(e.target.value)}
          required
        >
          <option value="Pilani">Pilani</option>
          <option value="Goa">Goa</option>
          <option value="Hyderabad">Hyderabad</option>
        </select>

        {/* Password Fields */}
        <input
          type="password"
          placeholder="Password"
          className="mb-3 p-2 border rounded w-full"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Confirm Password"
          className="mb-3 p-2 border rounded w-full"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <button
          type="submit"
          className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
        >
          Register
        </button>
      </form>
    </div>
  );
}
