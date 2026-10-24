type CandidateTask = { status: string; result?: unknown };

export function comparisonCandidateHint(tasks: readonly CandidateTask[], loading: boolean): string | null {
  const successful = tasks.filter(task => task.status === "success" && task.result).length;
  if (successful >= 2) return null;
  if (loading) return "正在刷新研究任务候选…";
  if (tasks.some(task => task.status === "pending" || task.status === "running")) {
    return "研究任务仍在执行，成功后候选会自动更新。";
  }
  return successful === 1 ? "还需完成一项研究任务才能生成对比。" : "至少完成两个研究任务后才能进行对比。";
}
