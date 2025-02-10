// components/FeeDetails.tsx
"use client";

import { useEffect, useState } from "react";

export default function FeeDetails() {
  const [fees, setFees] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const fetchFees = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/fees?query=${searchQuery}`,
        {
          method: "GET",
          credentials: "include",
        }
      );
      if (res.ok) {
        const data = await res.json();
        setFees(data);
      }
    } catch (error) {
      console.error("Failed to fetch fee details", error);
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
      <h1 className="text-3xl font-bold mb-4">Fee Details</h1>
      <div className="flex items-center mb-4">
        <input
          type="text"
          placeholder="Enter Application Number"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="p-2 border border-gray-300 rounded w-64"
        />
        <button
          className="ml-2 bg-blue-600 text-white px-4 py-2 rounded"
          onClick={fetchFees}
        >
          Search
        </button>
      </div>
      {loading && (
        <p className="text-center text-gray-600">Loading fee details...</p>
      )}
      {searched && fees.length === 0 && !loading && (
        <p className="text-center text-red-600">No fee details found</p>
      )}
      {!loading && fees.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-300 p-2">
                  Application Number
                </th>
                <th className="border border-gray-300 p-2">Iteration Number</th>
                <th className="border border-gray-300 p-2">Scholarship</th>
                <th className="border border-gray-300 p-2">
                  Admission Fees Amt.
                </th>
                <th className="border border-gray-300 p-2">
                  Tuition Fees Amt.
                </th>
              </tr>
            </thead>
            <tbody>
              {fees.map((fee, index) => (
                <tr key={index}>
                  <td className="border border-gray-300 p-2">
                    {fee.applicationNumber}
                  </td>
                  <td className="border border-gray-300 p-2">
                    {fee.iterationNumber}
                  </td>
                  <td className="border border-gray-300 p-2">
                    {fee.scholarship}
                  </td>
                  <td className="border border-gray-300 p-2">
                    {fee.admissionFeesAmount}
                  </td>
                  <td className="border border-gray-300 p-2">
                    {fee.tuitionFeesAmount}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
