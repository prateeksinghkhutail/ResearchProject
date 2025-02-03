// app/page.js
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import jwt from "jsonwebtoken";
import Navbar from "./components/Navbar.jsx";
import Homepage from "./components/Homepage.jsx";
import Footer from "./components/Footer.jsx";

export default async function HomePage() {
  // Check authentication (e.g., token stored in cookies)
  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  if (!token) {
    console.log("No token found, redirecting to login");
    redirect("/login");
  }

  try {
    const decoded = jwt.decode(token);
    if (decoded.exp * 1000 < Date.now()) {
      redirect("/login");
    }
  } catch (error) {
    redirect("/login");
  }

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-gray-50">
        <Homepage />
      </main>
      <Footer />
    </>
  );
}
