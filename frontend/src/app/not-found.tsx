import Link from 'next/link';

export default function NotFound(): React.JSX.Element {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <Link href="/">Go home</Link>
    </main>
  );
}
