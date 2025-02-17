"use client";

import { useState } from "react";

export default function IterationDetails() {
  const [iterations, setIterations] = useState([]);
  const [iterationQuery, setIterationQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const fetchIterations = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/iterations?iteration=${iterationQuery}`,
        {
          method: "GET",
          credentials: "include",
        }
      );
      if (res.ok) {
        const data = await res.json();
        if (data.message) {
          // If no iteration record is found
          setIterations([]);
        } else {
          setIterations(Array.isArray(data) ? data : [data]);
        }
      } else {
        console.error("Failed to fetch iterations", res);
      }
    } catch (error) {
      console.error("Failed to fetch iterations", error);
    }
    setLoading(false);
  };

  return (
    <div className="p-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold">
          Welcome, BITS Pilani - Pilani Campus
        </h1>
        <p className="text-gray-500 mb-6">
          Welcome to BITS Admission Portal Dashboard
        </p>
      </div>

      <h1 className="text-3xl font-bold mb-4">Iteration Details</h1>
      <div className="flex items-center mb-4">
        <input
          type="text"
          placeholder="Enter Iteration Number"
          value={iterationQuery}
          onChange={(e) => setIterationQuery(e.target.value)}
          className="p-2 border border-gray-300 rounded w-64"
        />
        <button
          className="ml-2 bg-blue-600 text-white px-4 py-2 rounded"
          onClick={fetchIterations}
        >
          Search
        </button>
      </div>

      {loading && (
        <p className="text-center text-gray-600">Loading iteration details...</p>
      )}
      {searched && iterations.length === 0 && !loading && (
        <p className="text-center text-red-600">No iteration found</p>
      )}
      {!loading && iterations.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6 overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300 text-sm">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-300 p-2">Application No</th>
                <th className="border border-gray-300 p-2">Iteration No</th>
                <th className="border border-gray-300 p-2">Offer</th>
                <th className="border border-gray-300 p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {iterations.map((iteration, index) => (
                <tr key={`${iteration.app_no}-${iteration.itr_no || index}`}>
                  <td className="border border-gray-300 p-2">{iteration.app_no}</td>
                  <td className="border border-gray-300 p-2">{iteration.itr_no}</td>
                  <td className="border border-gray-300 p-2">{iteration.offer}</td>
                  <td className="border border-gray-300 p-2">{iteration.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
