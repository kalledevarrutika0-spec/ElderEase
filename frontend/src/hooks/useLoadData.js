import { useCallback, useEffect, useState } from "react";

export default function useLoadData(loader, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await loader());
    } catch (loadError) {
      setError(loadError.message || "Unable to load this information.");
    } finally {
      setLoading(false);
    }
  // Loader identity is intentionally controlled by its dependency list.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
