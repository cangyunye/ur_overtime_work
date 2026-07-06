/* 加班登记系统 - 前端交互逻辑 */

(function () {
  "use strict";

  var currentPage = 1;

  // ---- 工具函数 ----

  /** 计算最近的周六 */
  function getNearestSaturday() {
    var today = new Date();
    var day = today.getDay(); // 0=周日, 6=周六
    // 如果今天是周六，返回今天；否则计算到下一个周六
    var diff = day === 6 ? 0 : (6 - day);
    var sat = new Date(today);
    sat.setDate(today.getDate() + diff);
    return formatDate(sat);
  }

  /** 格式化日期为 yyyy-mm-dd */
  function formatDate(d) {
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + day;
  }

  /** 计算本周一的日期 */
  function getCurrentWeekMonday() {
    var today = new Date();
    var day = today.getDay();
    var diff = day === 0 ? -6 : 1 - day;
    var monday = new Date(today);
    monday.setDate(today.getDate() + diff);
    return formatDate(monday);
  }

  /** 计算本周日的日期 */
  function getCurrentWeekSunday() {
    var today = new Date();
    var day = today.getDay();
    var diff = day === 0 ? 0 : 7 - day;
    var sunday = new Date(today);
    sunday.setDate(today.getDate() + diff);
    return formatDate(sunday);
  }

  /** 显示消息提示 */
  function showToast(message, type) {
    var toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = "toast " + (type || "success");
    // 强制重排以触发过渡
    toast.offsetHeight;
    toast.classList.add("show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () {
      toast.classList.remove("show");
    }, 3000);
  }

  // ---- 时段预设配置 ----
  // 键名对应 <select> 的 option value，添加新预设只需在此加一项
  var TIME_PRESETS = {
    day:   { start: "08:00:00", end: "17:30:00", label: "早班段" },
    night: { start: "09:00:00", end: "19:00:00", label: "晚班段" },
  };

  /** 根据选中预设填充开始/结束时间 */
  function applyTimePreset(key) {
    var date = document.getElementById("overtime_date").value;
    var t = TIME_PRESETS[key];
    if (!t) return;
    document.getElementById("start_time").value = (date ? date + " " : "") + t.start;
    document.getElementById("end_time").value = (date ? date + " " : "") + t.end;
  }

  function applyEditTimePreset(key) {
    var date = document.getElementById("edit_overtime_date").value;
    var t = TIME_PRESETS[key];
    if (!t) return;
    document.getElementById("edit_start_time").value = (date ? date + " " : "") + t.start;
    document.getElementById("edit_end_time").value = (date ? date + " " : "") + t.end;
  }

  function applyTimePresetFromCurrent() {
    var key = document.querySelector(".preset-group .preset-btn.active");
    if (key) applyTimePreset(key.getAttribute("data-preset"));
  }

  function setTimePreset(key, btn) {
    document.querySelectorAll(".preset-group .preset-btn").forEach(function (b) {
      b.classList.remove("active");
    });
    if (btn) btn.classList.add("active");
    applyTimePreset(key);
  }

  function setEditTimePreset(key, btn) {
    document.querySelectorAll("#editForm .preset-btn").forEach(function (b) {
      b.classList.remove("active");
    });
    if (btn) btn.classList.add("active");
    applyEditTimePreset(key);
  }

  /** 表单日期联动：当加班日期变化时，按当前时段预设填充时间 */
  function syncTimeDates() {
    var date = document.getElementById("overtime_date").value;
    if (date) {
      var startEl = document.getElementById("start_time");
      var endEl = document.getElementById("end_time");
      if (!startEl.value || !endEl.value) {
        applyTimePresetFromCurrent();
      }
    }
  }

  // ---- 自动关联：姓名/工号输入时填充最近登记信息 ----

  var autoFillTimer = null;
  var isAutoFilling = false;

  function triggerAutoFill() {
    if (isAutoFilling) return;
    clearTimeout(autoFillTimer);
    autoFillTimer = setTimeout(function () {
      var name = document.getElementById("employee_name").value.trim();
      var empId = document.getElementById("employee_id").value.trim();
      if (!name && !empId) return;

      var params = "";
      if (name) params += "name=" + encodeURIComponent(name);
      if (empId) params += (params ? "&" : "") + "employee_id=" + encodeURIComponent(empId);

      fetch("/api/auto-fill?" + params)
        .then(function (res) { return res.json(); })
        .then(function (result) {
          if (result.match && result.data) {
            isAutoFilling = true;
            var d = result.data;
            if (empId && d.employee_name) {
              document.getElementById("employee_name").value = d.employee_name;
            }
            if (!empId && name && d.employee_id) {
              document.getElementById("employee_id").value = d.employee_id;
            }
            document.getElementById("company").value = d.company || "";
            document.getElementById("project_team").value = d.project_team || "";
            document.getElementById("pm").value = d.pm || "";
            isAutoFilling = false;
          } else if (result.multiple) {
            showToast("找到多条同名记录，请输入工号进行精确匹配", "warning");
          }
        })
        .catch(function () {});
    }, 400);
  }

  document.getElementById("employee_name").addEventListener("input", triggerAutoFill);
  document.getElementById("employee_id").addEventListener("input", triggerAutoFill);

  // ---- 表单提交 ----

  document.getElementById("overtimeForm").addEventListener("submit", function (e) {
    e.preventDefault();
    clearErrors();

    var data = {
      employee_name: document.getElementById("employee_name").value.trim(),
      employee_id: document.getElementById("employee_id").value.trim(),
      company: document.getElementById("company").value.trim(),
      project_team: document.getElementById("project_team").value.trim(),
      pm: document.getElementById("pm").value.trim(),
      reason: document.getElementById("reason").value.trim(),
      overtime_date: document.getElementById("overtime_date").value,
      start_time: document.getElementById("start_time").value.trim(),
      end_time: document.getElementById("end_time").value.trim(),
    };

    // 前端校验
    var hasError = false;
    var required = ["employee_name", "employee_id", "company", "project_team", "pm", "reason", "overtime_date", "start_time", "end_time"];
    required.forEach(function (field) {
      if (!data[field]) {
        showFieldError(field, "此字段为必填项");
        hasError = true;
      }
    });

    if (hasError) return;

    if (!/^\d{4}-\d{2}-\d{2}$/.test(data.overtime_date)) {
      showFieldError("overtime_date", "格式应为 yyyy-mm-dd");
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(data.start_time)) {
      showFieldError("start_time", "格式应为 yyyy-mm-dd hh24:mi:ss");
      return;
    }
    if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(data.end_time)) {
      showFieldError("end_time", "格式应为 yyyy-mm-dd hh24:mi:ss");
      return;
    }
    if (data.end_time <= data.start_time) {
      showFieldError("end_time", "结束时间必须晚于开始时间");
      return;
    }

    var btn = document.getElementById("submitBtn");
    btn.disabled = true;
    btn.textContent = "提交中...";

    fetch("/api/records", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(function (res) { return res.json(); })
      .then(function (result) {
        btn.disabled = false;
        btn.textContent = "提交登记";
        if (result.error) {
          showToast(result.error, "error");
        } else {
          showToast("登记成功！", "success");
          resetForm();
          loadRecords(1);
        }
      })
      .catch(function () {
        btn.disabled = false;
        btn.textContent = "提交登记";
        showToast("网络错误，请重试", "error");
      });
  });

  // ---- 日期联动事件 ----

  document.getElementById("overtime_date").addEventListener("change", syncTimeDates);

  // ---- 表单操作 ----

  function resetForm() {
    document.getElementById("overtimeForm").reset();
    document.getElementById("overtime_date").value = getNearestSaturday();
    clearErrors();
    syncTimeDates();
  }

  function clearErrors() {
    var errEls = document.querySelectorAll(".error-text");
    errEls.forEach(function (el) { el.classList.remove("visible"); el.textContent = ""; });
    var inputEls = document.querySelectorAll("input.error");
    inputEls.forEach(function (el) { el.classList.remove("error"); });
  }

  function showFieldError(field, msg) {
    var errEl = document.getElementById("err_" + field);
    var inputEl = document.getElementById(field);
    if (errEl) { errEl.textContent = msg; errEl.classList.add("visible"); }
    if (inputEl) { inputEl.classList.add("error"); }
  }

  // ---- 记录列表 ----

  window.loadRecords = function (page) {
    currentPage = page || 1;
    var pageSize = parseInt(document.getElementById("pagination_page_size").value, 10) || 50;
    var dateFrom = document.getElementById("filter_date_from").value;
    var dateTo = document.getElementById("filter_date_to").value;
    var company = document.getElementById("filter_company").value.trim();
    var projectTeam = document.getElementById("filter_project_team").value.trim();
    var empId = document.getElementById("filter_employee_id").value.trim();
    var empName = document.getElementById("filter_employee_name").value.trim();

    var params = "page=" + currentPage + "&page_size=" + pageSize;
    if (dateFrom) params += "&date_from=" + encodeURIComponent(dateFrom);
    if (dateTo) params += "&date_to=" + encodeURIComponent(dateTo);
    if (company) params += "&company=" + encodeURIComponent(company);
    if (projectTeam) params += "&project_team=" + encodeURIComponent(projectTeam);
    if (empId) params += "&employee_id=" + encodeURIComponent(empId);
    if (empName) params += "&employee_name=" + encodeURIComponent(empName);

    var tbody = document.getElementById("recordsBody");
    tbody.innerHTML = '<tr><td colspan="12" class="empty-state"><div class="loading">加载中...</div></td></tr>';

    fetch("/api/records?" + params)
      .then(function (res) { return res.json(); })
      .then(function (result) {
        renderTable(result);
      })
      .catch(function () {
        tbody.innerHTML = '<tr><td colspan="12" class="empty-state"><p>加载失败，请刷新重试</p></td></tr>';
      });
  };

  function renderTable(result) {
    var tbody = document.getElementById("recordsBody");
    var records = result.records || [];
    document.getElementById("totalCount").textContent = result.total;

    if (records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="12" class="empty-state"><div class="icon">&#128203;</div><p>暂无加班记录</p></td></tr>';
      document.getElementById("pageBtns").innerHTML = "";
      return;
    }

    var html = "";
    var curPageSize = parseInt(document.getElementById("pagination_page_size").value, 10) || 50;
    records.forEach(function (r, idx) {
      html += '<tr>'
        + "<td>" + (result.total - (currentPage - 1) * curPageSize - idx) + "</td>"
        + "<td>" + escapeHtml(r.employee_name) + "</td>"
        + "<td>" + escapeHtml(r.employee_id) + "</td>"
        + "<td>" + escapeHtml(r.company) + "</td>"
        + "<td>" + escapeHtml(r.project_team) + "</td>"
        + "<td>" + escapeHtml(r.pm) + "</td>"
        + "<td title=\"" + escapeHtml(r.reason) + "\">" + truncate(escapeHtml(r.reason), 20) + "</td>"
        + "<td>" + escapeHtml(r.overtime_date) + "</td>"
        + "<td>" + escapeHtml(r.start_time.slice(-8)) + "</td>"
        + "<td>" + escapeHtml(r.end_time.slice(-8)) + "</td>"
        + "<td>" + escapeHtml(r.created_at) + "</td>"
        + '<td class="actions">'
        + '<button class="btn btn-outline btn-sm" onclick="openEdit(' + r.id + ')">编辑</button> '
        + '<button class="btn btn-danger btn-sm" onclick="deleteRecord(' + r.id + ')">删除</button>'
        + "</td>"
        + "</tr>";
    });
    tbody.innerHTML = html;
    renderPagination(result);
  }

  function renderPagination(result) {
    var container = document.getElementById("pageBtns");
    var totalPages = result.total_pages;
    if (totalPages <= 1) {
      container.innerHTML = "";
      return;
    }

    var html = '<button class="page-btn" onclick="loadRecords(' + (currentPage - 1) + ')"'
      + (currentPage <= 1 ? " disabled" : "") + ">上一页</button>";

    var start = Math.max(1, currentPage - 2);
    var end = Math.min(totalPages, currentPage + 2);
    if (start > 1) html += '<button class="page-btn" onclick="loadRecords(1)">1</button>';
    if (start > 2) html += '<span style="padding:0 0.3rem;color:var(--muted)">...</span>';

    for (var i = start; i <= end; i++) {
      html += '<button class="page-btn' + (i === currentPage ? " active" : "") + '" onclick="loadRecords(' + i + ')">' + i + "</button>";
    }

    if (end < totalPages - 1) html += '<span style="padding:0 0.3rem;color:var(--muted)">...</span>';
    if (end < totalPages) html += '<button class="page-btn" onclick="loadRecords(' + totalPages + ')">' + totalPages + "</button>";

    html += '<button class="page-btn" onclick="loadRecords(' + (currentPage + 1) + ')"'
      + (currentPage >= totalPages ? " disabled" : "") + ">下一页</button>";

    container.innerHTML = html;
  }

  // ---- 编辑功能 ----

  window.openEdit = function (id) {
    fetch("/api/records/" + id)
      .then(function (res) { return res.json(); })
      .then(function (result) {
        if (result.error) {
          showToast(result.error, "error");
          return;
        }
        document.getElementById("edit_id").value = result.id;
        document.getElementById("edit_employee_name").value = result.employee_name;
        document.getElementById("edit_employee_id").value = result.employee_id;
        document.getElementById("edit_company").value = result.company;
        document.getElementById("edit_project_team").value = result.project_team;
        document.getElementById("edit_pm").value = result.pm;
        document.getElementById("edit_reason").value = result.reason;
        document.getElementById("edit_overtime_date").value = result.overtime_date;
        document.getElementById("edit_start_time").value = result.start_time;
        document.getElementById("edit_end_time").value = result.end_time;
        document.getElementById("editModal").classList.add("active");
      })
      .catch(function () {
        showToast("加载记录失败", "error");
      });
  };

  window.closeModal = function () {
    document.getElementById("editModal").classList.remove("active");
  };

  window.saveEdit = function () {
    var id = document.getElementById("edit_id").value;
    var data = {
      employee_name: document.getElementById("edit_employee_name").value.trim(),
      employee_id: document.getElementById("edit_employee_id").value.trim(),
      company: document.getElementById("edit_company").value.trim(),
      project_team: document.getElementById("edit_project_team").value.trim(),
      pm: document.getElementById("edit_pm").value.trim(),
      reason: document.getElementById("edit_reason").value.trim(),
      overtime_date: document.getElementById("edit_overtime_date").value,
      start_time: document.getElementById("edit_start_time").value.trim(),
      end_time: document.getElementById("edit_end_time").value.trim(),
    };

    var required = ["employee_name", "employee_id", "company", "project_team", "pm", "reason", "overtime_date", "start_time", "end_time"];
    for (var i = 0; i < required.length; i++) {
      if (!data[required[i]]) {
        showToast(required[i] + " 为必填项", "error");
        return;
      }
    }

    fetch("/api/records/" + id, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(function (res) { return res.json(); })
      .then(function (result) {
        if (result.error) {
          showToast(result.error, "error");
        } else {
          showToast("更新成功", "success");
          closeModal();
          loadRecords(currentPage);
        }
      })
      .catch(function () {
        showToast("网络错误，请重试", "error");
      });
  };

  // ---- 删除功能 ----

  window.deleteRecord = function (id) {
    if (!confirm("确定要删除这条加班记录吗？")) return;

    fetch("/api/records/" + id, { method: "DELETE" })
      .then(function (res) { return res.json(); })
      .then(function (result) {
        if (result.error) {
          showToast(result.error, "error");
        } else {
          showToast("删除成功", "success");
          loadRecords(currentPage);
        }
      })
      .catch(function () {
        showToast("网络错误，请重试", "error");
      });
  };

  // ---- 导出 Excel ----

  window.exportExcel = function () {
    var dateFrom = document.getElementById("filter_date_from").value;
    var dateTo = document.getElementById("filter_date_to").value;
    var company = document.getElementById("filter_company").value.trim();
    var projectTeam = document.getElementById("filter_project_team").value.trim();
    var empId = document.getElementById("filter_employee_id").value.trim();
    var empName = document.getElementById("filter_employee_name").value.trim();

    var params = "";
    if (dateFrom) params += "&date_from=" + encodeURIComponent(dateFrom);
    if (dateTo) params += "&date_to=" + encodeURIComponent(dateTo);
    if (company) params += "&company=" + encodeURIComponent(company);
    if (projectTeam) params += "&project_team=" + encodeURIComponent(projectTeam);
    if (empId) params += "&employee_id=" + encodeURIComponent(empId);
    if (empName) params += "&employee_name=" + encodeURIComponent(empName);

    var url = "/api/records/export?" + (params ? params.substring(1) : "");
    showToast("正在导出，请稍候...", "success");
    window.location.href = url;
  };

  // ---- 筛选重置 ----

  window.resetFilters = function () {
    var monday = getCurrentWeekMonday();
    var sunday = getCurrentWeekSunday();
    document.getElementById("filter_date_from").value = monday;
    document.getElementById("filter_date_to").value = sunday;
    document.getElementById("filter_company").value = "";
    document.getElementById("filter_project_team").value = "";
    document.getElementById("filter_employee_id").value = "";
    document.getElementById("filter_employee_name").value = "";
    document.getElementById("pagination_page_size").value = "50";
    loadRecords(1);
  };

  window.resetForm = resetForm;
  window.applyTimePreset = applyTimePreset;
  window.applyEditTimePreset = applyEditTimePreset;
  window.setTimePreset = setTimePreset;
  window.setEditTimePreset = setEditTimePreset;

  // ---- 辅助函数 ----

  function escapeHtml(str) {
    if (!str) return "";
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function truncate(str, len) {
    if (str.length <= len) return str;
    return str.substring(0, len) + "...";
  }

  // ---- 点击弹窗外部关闭 ----

  document.getElementById("editModal").addEventListener("click", function (e) {
    if (e.target === this) closeModal();
  });

  // ---- 键盘 ESC 关闭弹窗 ----

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });

  // ---- 初始化 ----

  document.getElementById("overtime_date").value = getNearestSaturday();
  syncTimeDates();

  // 日期筛选默认显示本周一~本周日（仅提示，查询时用户点击"查询"才生效）
  document.getElementById("filter_date_from").value = getCurrentWeekMonday();
  document.getElementById("filter_date_to").value = getCurrentWeekSunday();
  // 初始加载时不带日期筛选，以免隐藏历史数据
  loadRecords(1);

})();
