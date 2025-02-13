'use client';

import { useEffect, useState } from 'react';

export default function IterationDetails() {
	const [iterations, setIterations] = useState([]);
	const [iterationCount, setIterationCount] = useState(0);
	const [selectedIteration, setSelectedIteration] = useState(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');

	// Fetch iteration count on component mount
	useEffect(() => {
		const fetchIterationCount = async () => {
			try {
				const res = await fetch('http://localhost:8000/api/iteration-count', {
					method: 'GET',
					credentials: 'include'
				});
				if (res.ok) {
					const data = await res.json();
					setIterationCount(data.count);
				} else {
					throw new Error('Failed to fetch iteration count');
				}
			} catch (error) {
				console.error(error);
				setError('Unable to load iteration count.');
			}
		};
		fetchIterationCount();
	}, []);

	// Function to fetch iteration details
	const fetchIterations = async iterationNumber => {
		setLoading(true);
		setError('');

		try {
			const res = await fetch(
				`http://localhost:8000/api/iterations?iteration=${iterationNumber}`,
				{
					method: 'GET',
					credentials: 'include'
				}
			);

			if (res.ok) {
				const data = await res.json();

				// If no iterations found, show message
				if (data.message) {
					setIterations([]);
					setError(data.message);
				} else {
					// Ensure Withdrawals are displayed properly
					const updatedIterations = data.map(iteration => ({
						...iteration,
						status:
							iteration.status === 'withdrawls' ? 'Withdrawn' : iteration.status
					}));

					setIterations(updatedIterations);
					setSelectedIteration(iterationNumber);
				}
			} else {
				throw new Error('Failed to fetch iteration details');
			}
		} catch (error) {
			console.error(error);
			setError('Unable to load iteration details.');
		}

		setLoading(false);
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

			<h1 className='text-3xl font-bold mb-4'>Iteration Details</h1>

			{error && <p className='text-center text-red-600'>{error}</p>}

			{iterationCount > 0 ? (
				<div className='flex flex-wrap gap-2 overflow-x-auto mb-4 p-2'>
					{[...Array(iterationCount).keys()].map(i => (
						<button
							key={i + 1}
							className={`px-4 py-2 rounded ${
								selectedIteration === i + 1
									? 'bg-blue-700 text-white'
									: 'bg-blue-600 text-white hover:bg-blue-700'
							}`}
							onClick={() => fetchIterations(i + 1)}>
							Iteration {i + 1}
						</button>
					))}
				</div>
			) : (
				<p className='text-center text-red-600'>
					No iterations have been conducted yet.
				</p>
			)}

			{loading && (
				<p className='text-center text-gray-600'>
					Loading iteration details...
				</p>
			)}

			{!loading && iterations.length > 0 && (
				<div className='bg-white shadow-md rounded-lg p-6 overflow-x-auto'>
					<table className='w-full border-collapse border border-gray-300'>
						<thead>
							<tr className='bg-gray-200'>
								<th className='border border-gray-300 p-2'>
									Application Number
								</th>
								<th className='border border-gray-300 p-2'>Iteration Number</th>
								<th className='border border-gray-300 p-2'>Offer</th>
								<th className='border border-gray-300 p-2'>Status</th>
							</tr>
						</thead>
						<tbody>
							{iterations.map((iteration, index) => (
								<tr key={index}>
									<td className='border border-gray-300 p-2'>
										{iteration.app_no}
									</td>
									<td className='border border-gray-300 p-2'>
										{iteration.itr_no}
									</td>
									<td className='border border-gray-300 p-2'>
										{iteration.offer}
									</td>
									<td
										className={`border border-gray-300 p-2 ${
											iteration.status === 'Withdrawn'
												? 'text-red-600 font-bold'
												: ''
										}`}>
										{iteration.status}
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
