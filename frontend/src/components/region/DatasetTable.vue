<template>
  <div class="table-shell">
    <div class="chart-header">
      <div>
        <h3>数据预览</h3>
        <p>显示当前数据集前 15 条记录，用于检查缺失值、数值范围和标签字段。</p>
      </div>
    </div>
    <div class="table-scroll">
      <table v-if="columns.length && rows.length">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column">{{ column }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in rows" :key="index">
            <td v-for="column in columns" :key="`${index}-${column}`">
              {{ row[column] ?? "-" }}
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty-text">暂无数据预览</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] }
});
</script>
