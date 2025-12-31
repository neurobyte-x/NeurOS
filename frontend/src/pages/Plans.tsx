import { useState, useEffect } from 'react';
import {
  Map,
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  PlayCircle,
  PauseCircle,
  ChevronRight,
  ChevronDown,
  Plus,
  Loader2,
  Milestone,
  BookOpen,
  ListTodo,
  Flame
} from 'lucide-react';
import { plansApi } from '../lib/api';
import type { 
  LearningPlan, 
  PlanMilestone, 
  WeeklySchedule,
  CreatePlanRequest,
  TodaysTasks
} from '../lib/types';
import { PLAN_TYPES } from '../lib/types';

const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700',
  active: 'bg-green-100 text-green-700',
  paused: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-blue-100 text-blue-700',
  abandoned: 'bg-red-100 text-red-700',
};

const MILESTONE_STATUS_ICONS = {
  not_started: <Circle className="w-5 h-5 text-gray-400" />,
  in_progress: <PlayCircle className="w-5 h-5 text-blue-500" />,
  completed: <CheckCircle2 className="w-5 h-5 text-green-500" />,
  skipped: <Circle className="w-5 h-5 text-gray-300" />,
};

export default function Plans() {
  const [plans, setPlans] = useState<LearningPlan[]>([]);
  const [todaysTasks, setTodaysTasks] = useState<TodaysTasks | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<(LearningPlan & {
    milestones: PlanMilestone[];
    weekly_schedules: WeeklySchedule[];
  }) | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null);

  // Create form state
  const [createForm, setCreateForm] = useState<CreatePlanRequest>({
    plan_type: 'dsa_fundamentals',
    primary_goal: '',
    target_weeks: 12,
    daily_time_minutes: 60,
    weekly_days: 5,
  });

  useEffect(() => {
    loadPlans();
    loadTodaysTasks();
  }, []);

  const loadPlans = async () => {
    try {
      const plansList = await plansApi.list();
      setPlans(plansList);
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTodaysTasks = async () => {
    try {
      const tasks = await plansApi.getToday();
      setTodaysTasks(tasks);
    } catch (error) {
      console.error('Failed to load today\'s tasks:', error);
    }
  };

  const loadPlanDetails = async (planId: number) => {
    try {
      const details = await plansApi.get(planId);
      setSelectedPlan(details);
    } catch (error) {
      console.error('Failed to load plan details:', error);
    }
  };

  const createPlan = async () => {
    if (!createForm.primary_goal) return;
    
    setGenerating(true);
    try {
      const newPlan = await plansApi.generate(createForm);
      setPlans(prev => [newPlan, ...prev]);
      setShowCreateModal(false);
      setCreateForm({
        plan_type: 'dsa_fundamentals',
        primary_goal: '',
        target_weeks: 12,
        daily_time_minutes: 60,
        weekly_days: 5,
      });
      // Load the new plan details
      loadPlanDetails(newPlan.id);
    } catch (error) {
      console.error('Failed to create plan:', error);
    } finally {
      setGenerating(false);
    }
  };

  const activatePlan = async (planId: number) => {
    try {
      await plansApi.activate(planId);
      loadPlans();
      if (selectedPlan?.id === planId) {
        loadPlanDetails(planId);
      }
    } catch (error) {
      console.error('Failed to activate plan:', error);
    }
  };

  const pausePlan = async (planId: number) => {
    try {
      await plansApi.pause(planId);
      loadPlans();
      if (selectedPlan?.id === planId) {
        loadPlanDetails(planId);
      }
    } catch (error) {
      console.error('Failed to pause plan:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Map className="w-8 h-8 text-primary-500" />
            Learning Plans
          </h1>
          <p className="text-gray-500 mt-1">
            AI-generated roadmaps to achieve your learning goals
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Create Plan
        </button>
      </div>

      {/* Today's Tasks */}
      {todaysTasks && todaysTasks.total_tasks > 0 && (
        <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <ListTodo className="w-5 h-5 text-primary-600" />
              Today's Tasks ({todaysTasks.day})
            </h2>
            <span className="text-sm text-gray-500">
              {todaysTasks.estimated_total_minutes} min total
            </span>
          </div>
          <div className="space-y-2">
            {todaysTasks.tasks.slice(0, 5).map((task, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-3 bg-white rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <Circle className="w-5 h-5 text-gray-300" />
                  <div>
                    <p className="font-medium">{task.title}</p>
                    <p className="text-sm text-gray-500">{task.plan_title}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Clock className="w-4 h-4" />
                  {task.estimated_minutes}m
                  {task.resource_url && (
                    <a 
                      href={task.resource_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:underline ml-2"
                    >
                      Open →
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Plans Grid */}
      <div className="grid grid-cols-3 gap-6">
        {/* Plans List */}
        <div className="col-span-1 space-y-4">
          <h2 className="text-lg font-semibold">Your Plans</h2>
          {plans.length === 0 ? (
            <div className="card text-center py-8 text-gray-500">
              <Map className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No plans yet</p>
              <p className="text-sm">Create your first learning plan!</p>
            </div>
          ) : (
            plans.map(plan => (
              <div
                key={plan.id}
                onClick={() => loadPlanDetails(plan.id)}
                className={`card cursor-pointer hover:shadow-md transition-all ${
                  selectedPlan?.id === plan.id ? 'ring-2 ring-primary-500' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{plan.title}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[plan.status]}`}>
                    {plan.status}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">{plan.primary_goal}</p>
                
                {/* Progress Bar */}
                <div className="mb-2">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">Progress</span>
                    <span className="font-medium">{plan.progress_percentage.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-500 h-2 rounded-full transition-all"
                      style={{ width: `${plan.progress_percentage}%` }}
                    />
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Week {plan.current_week}</span>
                  <span>{plan.completed_milestones}/{plan.total_milestones} milestones</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Plan Details */}
        <div className="col-span-2">
          {selectedPlan ? (
            <div className="card">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedPlan.title}</h2>
                  <p className="text-gray-600 mt-1">{selectedPlan.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  {selectedPlan.status === 'draft' && (
                    <button
                      onClick={() => activatePlan(selectedPlan.id)}
                      className="btn-primary flex items-center gap-1"
                    >
                      <PlayCircle className="w-4 h-4" />
                      Start Plan
                    </button>
                  )}
                  {selectedPlan.status === 'active' && (
                    <button
                      onClick={() => pausePlan(selectedPlan.id)}
                      className="btn-secondary flex items-center gap-1"
                    >
                      <PauseCircle className="w-4 h-4" />
                      Pause
                    </button>
                  )}
                  {selectedPlan.status === 'paused' && (
                    <button
                      onClick={() => activatePlan(selectedPlan.id)}
                      className="btn-primary flex items-center gap-1"
                    >
                      <PlayCircle className="w-4 h-4" />
                      Resume
                    </button>
                  )}
                </div>
              </div>

              {/* Plan Stats */}
              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Duration</p>
                  <p className="text-lg font-bold">
                    {selectedPlan.target_end_date 
                      ? `${Math.ceil((new Date(selectedPlan.target_end_date).getTime() - new Date(selectedPlan.start_date || new Date()).getTime()) / (7 * 24 * 60 * 60 * 1000))} weeks`
                      : 'Not set'}
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Daily Time</p>
                  <p className="text-lg font-bold">{selectedPlan.daily_time_minutes} min</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Days/Week</p>
                  <p className="text-lg font-bold">{selectedPlan.weekly_days} days</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Current Week</p>
                  <p className="text-lg font-bold">{selectedPlan.current_week}</p>
                </div>
              </div>

              {/* Milestones */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Milestone className="w-5 h-5" />
                  Milestones
                </h3>
                <div className="space-y-3">
                  {selectedPlan.milestones.map((milestone) => (
                    <div 
                      key={milestone.id}
                      className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg"
                    >
                      {MILESTONE_STATUS_ICONS[milestone.status]}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">{milestone.title}</h4>
                          <span className="text-sm text-gray-500">
                            ~{milestone.estimated_days} days
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                        {milestone.topics.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {milestone.topics.map((topic, i) => (
                              <span key={i} className="px-2 py-0.5 text-xs bg-white rounded">
                                {topic}
                              </span>
                            ))}
                          </div>
                        )}
                        {milestone.recommended_problems.length > 0 && (
                          <div className="mt-2 text-sm text-primary-600">
                            {milestone.recommended_problems.length} problems to solve
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Weekly Schedule */}
              {selectedPlan.weekly_schedules.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Weekly Schedule
                  </h3>
                  <div className="space-y-2">
                    {selectedPlan.weekly_schedules.slice(0, 8).map(week => (
                      <div key={week.id} className="border rounded-lg">
                        <button
                          onClick={() => setExpandedWeek(expandedWeek === week.week_number ? null : week.week_number)}
                          className="w-full flex items-center justify-between p-4 hover:bg-gray-50"
                        >
                          <div className="flex items-center gap-3">
                            {week.is_completed ? (
                              <CheckCircle2 className="w-5 h-5 text-green-500" />
                            ) : week.week_number === selectedPlan.current_week ? (
                              <Flame className="w-5 h-5 text-orange-500" />
                            ) : (
                              <Circle className="w-5 h-5 text-gray-300" />
                            )}
                            <div className="text-left">
                              <p className="font-medium">Week {week.week_number}: {week.theme || 'No theme'}</p>
                              <p className="text-sm text-gray-500">
                                {week.focus_areas.slice(0, 3).join(', ')}
                              </p>
                            </div>
                          </div>
                          {expandedWeek === week.week_number ? (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronRight className="w-5 h-5 text-gray-400" />
                          )}
                        </button>
                        
                        {expandedWeek === week.week_number && (
                          <div className="px-4 pb-4 border-t">
                            {week.weekly_goals.length > 0 && (
                              <div className="mt-3">
                                <p className="text-sm font-medium text-gray-700 mb-2">Goals:</p>
                                <ul className="list-disc list-inside text-sm text-gray-600">
                                  {week.weekly_goals.map((goal, i) => (
                                    <li key={i}>{goal}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {Object.entries(week.daily_tasks || {}).length > 0 && (
                              <div className="mt-3">
                                <p className="text-sm font-medium text-gray-700 mb-2">Daily Tasks:</p>
                                {Object.entries(week.daily_tasks).map(([day, tasks]) => (
                                  <div key={day} className="mb-2">
                                    <p className="text-xs font-medium text-gray-500 uppercase mb-1">
                                      {day}
                                    </p>
                                    <div className="space-y-1">
                                      {(tasks as any[]).map((task, i) => (
                                        <div key={i} className="flex items-center gap-2 text-sm p-2 bg-gray-50 rounded">
                                          <Circle className="w-3 h-3 text-gray-300" />
                                          <span>{task.title}</span>
                                          <span className="text-gray-400">({task.estimated_minutes}m)</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-16 text-gray-500">
              <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Select a plan to view details</p>
              <p className="text-sm">Or create a new plan to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Plan Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold">Create Learning Plan</h2>
              <p className="text-gray-500 text-sm">AI will generate a personalized roadmap based on your inputs</p>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Plan Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Plan Type
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {PLAN_TYPES.map(type => (
                    <button
                      key={type.value}
                      onClick={() => setCreateForm(prev => ({ ...prev, plan_type: type.value }))}
                      className={`p-3 text-left rounded-lg border transition-colors ${
                        createForm.plan_type === type.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <p className="font-medium text-sm">{type.label}</p>
                      <p className="text-xs text-gray-500">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Primary Goal */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Goal *
                </label>
                <textarea
                  value={createForm.primary_goal}
                  onChange={e => setCreateForm(prev => ({ ...prev, primary_goal: e.target.value }))}
                  placeholder="E.g., Crack FAANG interviews in 3 months, Reach Expert on Codeforces..."
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                />
              </div>

              {/* Time Settings */}
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Duration (weeks)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={52}
                    value={createForm.target_weeks}
                    onChange={e => setCreateForm(prev => ({ 
                      ...prev, 
                      target_weeks: parseInt(e.target.value) || 12 
                    }))}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Daily Time (minutes)
                  </label>
                  <input
                    type="number"
                    min={15}
                    max={480}
                    value={createForm.daily_time_minutes}
                    onChange={e => setCreateForm(prev => ({ 
                      ...prev, 
                      daily_time_minutes: parseInt(e.target.value) || 60 
                    }))}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Days per Week
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={7}
                    value={createForm.weekly_days}
                    onChange={e => setCreateForm(prev => ({ 
                      ...prev, 
                      weekly_days: parseInt(e.target.value) || 5 
                    }))}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>

              {/* Current Levels */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Skill Levels (1-10, optional)
                </label>
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { key: 'current_dsa_level', label: 'DSA' },
                    { key: 'current_cp_level', label: 'CP' },
                    { key: 'current_backend_level', label: 'Backend' },
                    { key: 'current_ai_ml_level', label: 'AI/ML' },
                  ].map(field => (
                    <div key={field.key}>
                      <label className="text-xs text-gray-500">{field.label}</label>
                      <input
                        type="number"
                        min={1}
                        max={10}
                        placeholder="1-10"
                        value={(createForm as any)[field.key] || ''}
                        onChange={e => setCreateForm(prev => ({ 
                          ...prev, 
                          [field.key]: e.target.value ? parseInt(e.target.value) : undefined 
                        }))}
                        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={createPlan}
                disabled={!createForm.primary_goal || generating}
                className="btn-primary flex items-center gap-2"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Map className="w-5 h-5" />
                    Generate Plan
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}