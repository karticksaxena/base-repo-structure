'use client'; // replaces the root layout when it fails, so it renders its own <html> and <body>

export default function GlobalError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}): React.JSX.Element {
  return (
    <html lang="en">
      <body>
        <h1>Something went wrong</h1>
        {error.digest ? <p>Error ID: {error.digest}</p> : null}
        <button type="button" onClick={retry}>
          Try again
        </button>
      </body>
    </html>
  );
}
