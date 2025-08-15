export function Avatar({ children }) {
  return (
    <div
      style={{
        borderRadius: "50%",
        overflow: "hidden",
        width: 40,
        height: 40,
        display: "inline-block",
      }}
    >
      {children}
    </div>
  );
}