type ErrorMessageProps = {
  title?: string;
  message: string;
};

function ErrorMessage({ title = "Something needs attention", message }: ErrorMessageProps) {
  return (
    <section className="error-state" role="alert">
      <strong>{title}</strong>
      <p>{message}</p>
    </section>
  );
}

export default ErrorMessage;
