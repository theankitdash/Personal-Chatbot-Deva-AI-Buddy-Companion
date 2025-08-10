export function Input(props) {
  return (
    <input
      {...props}
      className={`border rounded px-3 py-2 focus:outline-none focus:ring ${props.className || ""}`}
    />
  );
}
