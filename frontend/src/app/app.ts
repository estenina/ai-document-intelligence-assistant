import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { DocumentApiService } from './services/document-api.service';

interface Citation {
  source_text: string;
}

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly documentApi = inject(DocumentApiService);

  // Document
  selectedFile = signal<File | null>(null);
  documentId = signal<string | null>(null);

  // Upload
  isUploading = signal(false);
  uploadMessage = signal('');

  // Summary
  summary = signal('');
  isGeneratingSummary = signal(false);

  // Ask AI
  question = '';
  answer = signal('');
  isThinking = signal(false);

  // Supporting Sources
  citations = signal<Citation[]>([]);
  foundInDocument = signal(false);

  // Error
  errorMessage = signal('');

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length > 0) {
      const file = input.files[0];

      this.selectedFile.set(file);

      // Reset previous document data
      this.documentId.set(null);
      this.summary.set('');
      this.question = '';
      this.answer.set('');
      this.citations.set([]);
      this.foundInDocument.set(false);
      this.uploadMessage.set('');
      this.errorMessage.set('');

      // Reset loading states
      this.isUploading.set(false);
      this.isGeneratingSummary.set(false);
      this.isThinking.set(false);
    }
  }

  uploadDocument(): void {
    const file = this.selectedFile();

    if (!file || this.isUploading()) {
      return;
    }

    // Start upload
    this.isUploading.set(true);

    // Clear previous results and errors
    this.uploadMessage.set('');
    this.errorMessage.set('');
    this.summary.set('');
    this.answer.set('');
    this.citations.set([]);
    this.foundInDocument.set(false);

    this.documentApi
      .uploadDocument(file)
      .subscribe({
        next: (response: any) => {
          console.log(
            'Upload successful:',
            response
          );

          // Save document ID
          this.documentId.set(
            response.document_id
          );

          // Upload finished
          this.isUploading.set(false);

          this.uploadMessage.set(
            'Document uploaded successfully.'
          );

          console.log(
            'Document ID saved:',
            this.documentId()
          );

          // Automatically generate summary
          this.summarizeDocument();
        },

        error: (error) => {
          console.error(
            'Upload failed:',
            error
          );

          // Stop loading
          this.isUploading.set(false);

          // Get validation message from FastAPI
          const backendMessage =
            error?.error?.detail;

          // If backend provides a specific
          // validation message, show it
          if (backendMessage) {
            this.errorMessage.set(
              backendMessage
            );
          }

          // Handle files larger than 10 MB
          else if (error.status === 413) {
            this.errorMessage.set(
              'File is too large. Maximum file size is 10 MB.'
            );
          }

          // Generic fallback
          else {
            this.errorMessage.set(
              'Unable to analyze document. Please try again.'
            );
          }
        }
      });
  }

  summarizeDocument(): void {
    const id = this.documentId();

    if (
      !id ||
      this.isGeneratingSummary()
    ) {
      return;
    }

    // Start summary generation
    this.isGeneratingSummary.set(true);

    // Clear previous summary and error
    this.summary.set('');
    this.errorMessage.set('');

    this.documentApi
      .summarizeDocument(id)
      .subscribe({
        next: (response: any) => {
          console.log(
            'Summary successful:',
            response
          );

          // Save summary
          this.summary.set(
            response.summary
          );

          // Stop loading
          this.isGeneratingSummary.set(false);

          console.log(
            'Summary saved:',
            this.summary()
          );
        },

        error: (error) => {
          console.error(
            'Summary failed:',
            error
          );

          // Stop loading
          this.isGeneratingSummary.set(false);

          // Show user-friendly error
          this.errorMessage.set(
            'Unable to analyze document. Please try again.'
          );
        }
      });
  }

  askQuestion(): void {
    const id = this.documentId();

    const currentQuestion =
      this.question.trim();

    if (
      !id ||
      !currentQuestion ||
      this.isThinking()
    ) {
      return;
    }

    // Start thinking
    this.isThinking.set(true);

    // Clear previous answer, sources and error
    this.answer.set('');
    this.citations.set([]);
    this.foundInDocument.set(false);
    this.errorMessage.set('');

    this.documentApi
      .askQuestion(
        id,
        currentQuestion
      )
      .subscribe({
        next: (response: any) => {
          console.log(
            'Question response:',
            response
          );

          // Save AI answer
          this.answer.set(
            response.result.answer
          );

          // Save supporting citations
          this.citations.set(
            response.result.citations || []
          );

          // Save whether answer was found
          // in the uploaded document
          this.foundInDocument.set(
            response.result.found_in_document
          );

          // Stop thinking
          this.isThinking.set(false);

          console.log(
            'Answer saved:',
            this.answer()
          );

          console.log(
            'Found in document:',
            this.foundInDocument()
          );

          console.log(
            'Citations saved:',
            this.citations()
          );
        },

        error: (error) => {
          console.error(
            'Question failed:',
            error
          );

          // Stop thinking
          this.isThinking.set(false);

          // Show user-friendly error
          this.errorMessage.set(
            'Unable to answer your question. Please try again.'
          );
        }
      });
  }
}