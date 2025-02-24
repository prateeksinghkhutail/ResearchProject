'use client';

import { useState } from 'react';

export default function StudentDetails() {
	const [students, setStudents] = useState([]);
	const [searchQuery, setSearchQuery] = useState('');
	const [loading, setLoading] = useState(false);
	const [searched, setSearched] = useState(false);
	const [latestIteration, setLatestIteration] = useState(null);

	const fetchStudents = async () => {
		setLoading(true);
		setSearched(true);
		try {
			const res = await fetch(
				`http://localhost:8000/api/students?query=${searchQuery}`,
				{
					method: 'GET',
					credentials: 'include'
				}
			);
			if (res.ok) {
				const data = await res.json();
				if (Array.isArray(data) && data.length > 0) {
					// Find the latest iteration
					const maxIteration = Math.max(
						...data.map(student => student.itr_no || 0)
					);
					setLatestIteration(maxIteration);

					setStudents(data);
				}
				if (data.message) {
					// If no student record is found
					setStudents([]);
				} else {
					setStudents(Array.isArray(data) ? data : [data]);
				}
			} else {
				console.error('Failed to fetch students', res);
			}
		} catch (error) {
			console.error('Failed to fetch students', error);
		}
		setLoading(false);
	};

	const handleWithdraw = async (appNo, name) => {
		const confirmWithdraw = window.confirm(
			`Are you sure you want to withdraw ${name} (Application No: ${appNo})?`
		);

		if (!confirmWithdraw) return;

		try {
			const res = await fetch('http://localhost:8000/api/withdraw/student', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include',
				body: JSON.stringify({ app_no: appNo })
			});

			const data = await res.json();

			if (res.ok) {
				alert(`Application No: ${appNo} successfully withdrawn.`);
				fetchStudents(); // Refresh the student list
			} else {
				alert(`Failed to withdraw: ${data.detail}`);
			}
		} catch (error) {
			console.error('Error withdrawing application:', error);
			alert('Error processing withdrawal.');
		}
	};

	return (
		<div className='p-6'>
			<div className='text-center'>
				<h1 className='text-3xl font-bold'>
					Welcome, BITS Pilani - Pilani Campus
				</h1>
				<p className='text-gray-500 mb-6'>
					Welcome to BITS Admission Portal Dashboard
				</p>
			</div>

			<h1 className='text-3xl font-bold mb-4'>Student Details</h1>
			<div className='flex items-center mb-4'>
				<input
					type='text'
					placeholder='Enter Student ID or Name'
					value={searchQuery}
					onChange={e => setSearchQuery(e.target.value)}
					className='p-2 border border-gray-300 rounded w-64'
				/>
				<button
					className='ml-2 bg-blue-600 text-white px-4 py-2 rounded'
					onClick={fetchStudents}>
					Search
				</button>
			</div>

			{loading && (
				<p className='text-center text-gray-600'>Loading student details...</p>
			)}
			{searched && students.length === 0 && !loading && (
				<p className='text-center text-red-600'>No student found</p>
			)}
			{!loading && students.length > 0 && (
				<div className='bg-white shadow-md rounded-lg p-6 overflow-x-auto'>
					<table className='w-full border-collapse border border-gray-300 text-sm'>
						<thead>
							<tr className='bg-gray-200'>
								<th className='border border-gray-300 p-2'>Student ID</th>
								<th className='border border-gray-300 p-2'>Name</th>
								<th className='border border-gray-300 p-2'>Iteration No</th>
								<th className='border border-gray-300 p-2'>Offer</th>
								<th className='border border-gray-300 p-2'>Scholarship</th>
								<th className='border border-gray-300 p-2'>Status</th>
								<th className='border border-gray-300 p-2'>Action</th>
								{/* New Withdraw Button Column */}
							</tr>
						</thead>
						<tbody>
							{students.map((student, index) => (
								<tr
								key={`${student.app_no}-${student.itr_no || index}`}
								className={
									index % 2 === 0
										? 'bg-white hover:bg-blue-100'
										: 'bg-blue-50 hover:bg-blue-100'
								}
							>
									<td className='border border-gray-300 p-2'>
										{student.app_no}
									</td>
									<td className='border border-gray-300 p-2'>{student.name}</td>
									<td className='border border-gray-300 p-2'>
										{student.itr_no}
									</td>
									<td className='border border-gray-300 p-2'>
										{student.offer}
									</td>
									<td className='border border-gray-300 p-2'>
										{student.scholarship}
									</td>
									<td className='border border-gray-300 p-2'>
										{student.status}
									</td>

									
									<td className='border border-gray-300 p-2 text-center'>
										{student.itr_no === latestIteration && (
											<button
												className='bg-red-600 text-white px-3 py-1 rounded mx-auto block'
												onClick={() =>
													handleWithdraw(student.app_no, student.name)
												}>
												Withdraw
											</button>
										)}
									</td>
									{/* Withdraw Button */}
								</tr>
							))}
						</tbody>
					</table>
				</div>
			)}
		</div>
	);
}
