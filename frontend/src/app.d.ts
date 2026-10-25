// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

export {};

/// <reference types="@sveltejs/kit" />

// If the error persists, you can explicitly define the module right below it:
declare module "$env/static/public" {
  export const PUBLIC_API_URL: string;
}
