import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class DocumentApiService {
  private readonly http = inject(HttpClient);

  private readonly apiUrl = 'http://127.0.0.1:8000/documents';

  uploadDocument(file: File) {
    const formData = new FormData();

    formData.append('file', file);

    return this.http.post(
      `${this.apiUrl}/upload`,
      formData
    );
  }
  summarizeDocument(documentId: string) {
  return this.http.post(
    `${this.apiUrl}/${documentId}/summarize`,
    {}
  );
}
askQuestion(documentId: string, question: string) {
  return this.http.post(
    `${this.apiUrl}/${documentId}/questions`,
    {
      question: question
    }
  );
}
}