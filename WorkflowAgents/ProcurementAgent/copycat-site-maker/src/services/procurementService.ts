export async function procure(productList: string, location: string) {
  const formData = new FormData();
  formData.append('product_list', productList);
  formData.append('location', location);

  const response = await fetch('http://localhost:8000/procure', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to fetch procurement data');
  }

  return response.json();
}

export function downloadCSV() {
  window.open('http://localhost:8000/csv', '_blank');
} 