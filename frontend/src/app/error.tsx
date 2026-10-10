'use client'; // error boundaries must be Client Components

export default function ErrorPage({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}): React.JSX.Element {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      {error.digest ? <p className="text-sm">Error ID: {error.digest}</p> : null}
      <button type="button" onClick={retry}>
        Try again
      </button>
    </main>
  );
}
