"use client";

import { useState, useRef, useEffect } from "react";
import { redirect, useRouter } from "next/navigation";

export default function Homepage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadType, setUploadType] = useState(null);
  const [stats, setStats] = useState({
    totalApplications: 0,
    acceptedStudents: 0,
    iterationNumber: 0,
    iterationDate: "",
  });
  const fileUploadRef = useRef(null);
  const router = useRouter();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/stats", {
          method: "GET",
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          console.log(data);
          setStats({
            totalApplications: data.totalApplications,
            acceptedStudents: data.acceptedStudents,
            iterationNumber: data.latestIterationNumber,
            iterationDate: new Date(
              data.latestIterationDate
            ).toLocaleDateString(),
          });
        }
      } catch (error) {
        console.error("Failed to fetch stats", error);
      }
    };
    fetchStats();
  }, []);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = (fileType) => {
    setUploadType(fileType);
    setSelectedFile(null);
  };

  const submitFile = async () => {
    if (!selectedFile) {
      alert("Please select a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    let endpoint = "";
    if (uploadType === "master") {
      endpoint = "/update/MASTER_TABLE";
    } else if (uploadType === "iteration") {
      endpoint = "/update/ITERATION_OFFER";
    } else if (uploadType === "fees") {
      endpoint = "/update/FEES_PAID";
    }

    const res = await fetch(`http://localhost:8000${endpoint}`, {
      method: "POST",
      body: formData,
    });

    if (res.ok) {
      alert("File uploaded successfully");
      window.location.reload();
    } else {
      alert("File upload failed");
    }
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        fileUploadRef.current &&
        !fileUploadRef.current.contains(event.target)
      ) {
        setUploadType(null);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        <div className="bg-gray-200 p-6 rounded-lg w-full min-h-[200px] flex flex-col justify-center">
          <h3 className="text-lg font-semibold">Total Applications Received</h3>
          <p className="text-4xl font-bold">{stats.totalApplications}</p>
          <h3 className="text-lg font-semibold mt-4">
            Currently Accepted Students
          </h3>
          <p className="text-4xl font-bold">{stats.acceptedStudents}</p>
        </div>

        <div className="bg-gray-200 p-6 rounded-lg w-full min-h-[200px] flex flex-col justify-center">
          <h3 className="text-lg font-semibold">Current Iteration Stats</h3>
          <p className="text-4xl font-bold">{stats.iterationNumber}</p>
          <h3 className="text-lg font-semibold mt-4">Iteration Date</h3>
          <p className="text-3xl font-bold">{stats.iterationDate}</p>
        </div>
      </div>

      <div className="bg-gray-200 p-6 rounded-lg w-full mt-6 flex flex-col items-center">
        <h3 className="text-lg font-semibold">Upload CSV Files</h3>
        <div className="flex gap-4 mt-4">
          <button
            className={`w-48 py-2 rounded ${
              uploadType === "master"
                ? "bg-green-600 text-white"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
            onClick={() => handleUpload("master")}
          >
            Upload Master File
          </button>
          <button
            className={`w-48 py-2 rounded ${
              uploadType === "iteration"
                ? "bg-green-600 text-white"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
            onClick={() => handleUpload("iteration")}
          >
            Upload Iteration File
          </button>
          <button
            className={`w-48 py-2 rounded ${
              uploadType === "fees"
                ? "bg-green-600 text-white"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
            onClick={() => handleUpload("fees")}
          >
            Upload Fee Detail File
          </button>
        </div>
        {uploadType && (
          <div
            ref={fileUploadRef}
            className="mt-4 bg-white p-6 rounded shadow-md w-1/2 text-center"
          >
            <input
              type="file"
              className="w-full p-2 border rounded mb-2"
              onChange={handleFileChange}
            />
            <button
              className="w-full bg-green-500 hover:bg-green-600 text-white py-2 rounded"
              onClick={submitFile}
            >
              Submit File
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
