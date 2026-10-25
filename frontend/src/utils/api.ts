const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:5001").replace(/\/+$/, "");

export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const requestUrl = input instanceof Request ? input.url : input.toString();
  const url = new URL(requestUrl, `${API_BASE_URL}/`);
  const response = await fetch(url, {
    ...init,
    credentials: "include",
  });

  if (response.status === 401) {
    window.location.assign(`${API_BASE_URL}/logout`);
    throw new Error("Unauthorized");
  }

  return response;
}
