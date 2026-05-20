import { useCallback, useEffect, useState } from "react";
import type { ApiMeta, JobSummary } from "./api";
import { getMeta, listJobs } from "./api";
import { ConsoleShell } from "./components/layout/ConsoleShell";
import { RuntimeGate } from "./components/layout/RuntimeGate";
import { Sidebar, type Route } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { useTheme } from "./hooks/useTheme";
import { ComposerView } from "./views/ComposerView";
import { DiagnosticsView } from "./views/DiagnosticsView";
import { JobDetailView } from "./views/JobDetailView";
import { JobsView } from "./views/JobsView";
import { MicView } from "./views/MicView";

export function App() {
  const { theme, toggle: toggleTheme } = useTheme();
  const [meta, setMeta] = useState<ApiMeta | null>(null);
  const [metaErr, setMetaErr] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [route, setRoute] = useState<Route>("new");
  const [jobs, setJobs] = useState<JobSummary[]>([]);

  const loadMeta = useCallback(() => {
    setMetaErr(null);
    setRefreshing(true);
    void getMeta()
      .then(setMeta)
      .catch((e: unknown) => setMetaErr(e instanceof Error ? e.message : String(e)))
      .finally(() => setRefreshing(false));
  }, []);

  const loadJobs = useCallback(() => {
    void listJobs()
      .then(setJobs)
      .catch(() => setJobs([]));
  }, []);

  useEffect(() => {
    loadMeta();
  }, [loadMeta]);

  useEffect(() => {
    loadJobs();
    const id = window.setInterval(loadJobs, 3000);
    return () => window.clearInterval(id);
  }, [loadJobs]);

  const runtimeOk =
    !meta ||
    (meta.container_runtime === true && meta.subprocess_torch_import_ok !== false);
  const activeJobs = jobs.filter((j) => j.state === "running" || j.state === "queued");
  const runningCount = jobs.filter((j) => j.state === "running").length;

  const openJob = useCallback((id: string) => setRoute({ job: id }), []);
  const onJobStarted = useCallback(
    (jobId: string) => {
      loadJobs();
      setRoute({ job: jobId });
    },
    [loadJobs],
  );

  let main = null;
  if (runtimeOk) {
    if (typeof route === "object") {
      main = <JobDetailView jobId={route.job} onBack={() => setRoute("jobs")} />;
    } else if (route === "new") {
      main = <ComposerView meta={meta} onJobStarted={onJobStarted} />;
    } else if (route === "mic") {
      main = <MicView meta={meta} />;
    } else if (route === "jobs") {
      main = <JobsView jobs={jobs} onOpenJob={openJob} onNewJob={() => setRoute("new")} />;
    } else if (route === "diag") {
      main = (
        <DiagnosticsView meta={meta} metaErr={metaErr} onRefresh={loadMeta} refreshing={refreshing} />
      );
    }
  }

  return (
    <ConsoleShell
      topbar={
        <TopBar
          meta={meta}
          metaErr={metaErr}
          theme={theme}
          onToggleTheme={toggleTheme}
          onRefresh={loadMeta}
          refreshing={refreshing}
        />
      }
      sidebar={
        <Sidebar
          route={route}
          onRoute={setRoute}
          activeJobCount={activeJobs.length}
          runningCount={runningCount}
        />
      }
    >
      <RuntimeGate meta={meta} metaErr={metaErr}>
        {main}
      </RuntimeGate>
    </ConsoleShell>
  );
}
