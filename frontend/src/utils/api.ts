export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const response = await fetch(input, {
    ...init,
    credentials: "include",
  });

  if (response.status === 401) {
    window.location.assign("http://localhost:5001/logout");
    throw new Error("Unauthorized");
  }

  return response;
}
