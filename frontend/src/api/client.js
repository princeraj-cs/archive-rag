const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function parseResponse(response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail || "The request could not be completed.");
  }
  return body;
}

export async function queryDocs(
  question,
  history = [],
  enabledDocumentIds = null,
) {
  const response = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      history,
      enabled_document_ids: enabledDocumentIds,
    }),
  });
  return parseResponse(response);
}

export function uploadDoc(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `${API_URL}/upload`);
    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable)
        onProgress?.(Math.round((event.loaded / event.total) * 100));
    });
    request.addEventListener("load", () => {
      let body = {};
      try {
        body = JSON.parse(request.responseText);
      } catch {
        // Let the generic request error handle an invalid response body.
      }
      if (request.status >= 200 && request.status < 300) resolve(body);
      else
        reject(new Error(body.detail || "The upload could not be completed."));
    });
    request.addEventListener("error", () =>
      reject(new Error("The upload could not be completed.")),
    );
    request.send(formData);
  });
}

export async function getSources() {
  const response = await fetch(`${API_URL}/sources`);
  return parseResponse(response);
}

export async function deleteSource(documentId) {
  const response = await fetch(`${API_URL}/sources/${documentId}`, {
    method: "DELETE",
  });
  return parseResponse(response);
}
