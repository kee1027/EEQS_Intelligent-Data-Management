<template>
  <div class="app-container">
    <el-card class="manual-data-card">
      <div slot="header" class="clearfix">
        <span>数据录入</span>
      </div>

      <el-form
        v-permission="['operator', 'admin']"
        ref="manualDataForm"
        :model="form"
        :rules="rules"
        label-width="110px"
        class="manual-data-form"
      >
        <el-form-item label="操作人">
          <el-input :value="operatorName" disabled />
        </el-form-item>

        <el-form-item label="操作时间">
          <el-input :value="operatedAtDisplay" disabled />
        </el-form-item>

        <el-form-item label="数据时间" prop="data_at">
          <el-date-picker
            v-model="form.data_at"
            type="datetime"
            format="yyyy-MM-dd HH:mm:ss"
            placeholder="请选择数据时间"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="数据值" prop="value">
          <el-input v-model.trim="form.value" placeholder="请输入数据值（如 12.340000）" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submitForm">提交</el-button>
          <el-button :disabled="submitting" @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="query-header">
        <span class="query-title">记录查询</span>
        <el-button size="mini" :loading="loadingList" @click="loadRecords">刷新</el-button>
      </div>

      <el-table
        v-loading="loadingList"
        border
        stripe
        :data="records"
        :header-cell-style="{ background: 'var(--primary-bg-color)', color: 'var(--primary-color)', textAlign: 'center' }"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="operator" label="操作人" width="120" align="center" />
        <el-table-column prop="operated_at" label="操作时间" min-width="170" align="center" />
        <el-table-column prop="data_at" label="数据时间" min-width="170" align="center" />
        <el-table-column prop="value" label="数据值" width="120" align="center" />
        <el-table-column label="是否作废" width="90" align="center">
          <template slot-scope="scope">
            <span>{{ scope.row.is_void ? '是' : '否' }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="canOperate" label="操作" width="130" align="center">
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="danger"
              :loading="voidingIds.includes(scope.row.id)"
              :disabled="scope.row.is_void"
              @click="voidRecord(scope.row)"
            >
              作废
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { createManualData, listManualData, voidManualData } from '@/api/manual-data'

export default {
  name: 'ManualData',
  data() {
    return {
      submitting: false,
      loadingList: false,
      voidingIds: [],
      form: {
        data_at: '',
        value: ''
      },
      records: [],
      rules: {
        data_at: [{ required: true, message: '请选择数据时间', trigger: 'change' }],
        value: [
          { required: true, message: '请输入数据值', trigger: 'blur' },
          {
            pattern: /^-?\d+(\.\d+)?$/,
            message: '数据值需为数字',
            trigger: 'blur'
          }
        ]
      }
    }
  },
  computed: {
    operatorName() {
      return this.$store.getters.name || '-'
    },
    operatedAtDisplay() {
      return this.formatDate(new Date())
    },
    canOperate() {
      return ['operator', 'admin'].includes(this.$store.getters.role)
    }
  },
  mounted() {
    this.loadRecords()
  },
  methods: {
    formatDate(date) {
      const year = date.getFullYear()
      const month = `${date.getMonth() + 1}`.padStart(2, '0')
      const day = `${date.getDate()}`.padStart(2, '0')
      const hour = `${date.getHours()}`.padStart(2, '0')
      const minute = `${date.getMinutes()}`.padStart(2, '0')
      const second = `${date.getSeconds()}`.padStart(2, '0')
      return `${year}-${month}-${day} ${hour}:${minute}:${second}`
    },
    formatDateToIsoWithOffset(date) {
      const d = new Date(date)
      const year = d.getFullYear()
      const month = `${d.getMonth() + 1}`.padStart(2, '0')
      const day = `${d.getDate()}`.padStart(2, '0')
      const hour = `${d.getHours()}`.padStart(2, '0')
      const minute = `${d.getMinutes()}`.padStart(2, '0')
      const second = `${d.getSeconds()}`.padStart(2, '0')
      const offsetMin = -d.getTimezoneOffset()
      const sign = offsetMin >= 0 ? '+' : '-'
      const absOffset = Math.abs(offsetMin)
      const offsetHour = `${Math.floor(absOffset / 60)}`.padStart(2, '0')
      const offsetMinute = `${absOffset % 60}`.padStart(2, '0')
      return `${year}-${month}-${day}T${hour}:${minute}:${second}${sign}${offsetHour}:${offsetMinute}`
    },
    submitForm() {
      this.$refs.manualDataForm.validate(async (valid) => {
        if (!valid) return

        this.submitting = true
        try {
          const { data: result } = await createManualData({
            data_at: this.formatDateToIsoWithOffset(this.form.data_at),
            value: this.form.value
          })
          if (result && result.superseded_id) {
            this.$message.success('提交成功：已覆盖旧记录（原记录已作废留痕）')
          } else {
            this.$message.success('提交成功')
          }
          this.loadRecords()
        } catch (error) {
          const status = error && error.response && error.response.status
          if (status === 409) {
            this.$message.error('提交冲突，请刷新后重试')
          } else if (status === 403) {
            this.$message.error('需要操作员或管理员权限')
          } else if (status === 400) {
            this.$message.error('参数错误，请检查数据时间和数据值')
          } else {
            this.$message.error('提交失败，请稍后重试')
          }
        } finally {
          this.submitting = false
        }
      })
    },
    resetForm() {
      this.$refs.manualDataForm.resetFields()
    },
    async loadRecords() {
      this.loadingList = true
      try {
        const { data: result } = await listManualData()
        const rows = result.data || result.results || result || []
        this.records = Array.isArray(rows) ? rows : []
      } catch (error) {
        this.$message.error('查询记录失败')
      } finally {
        this.loadingList = false
      }
    },
    async voidRecord(record) {
      if (!record || !record.id || record.is_void) return

      this.voidingIds.push(record.id)
      try {
        await voidManualData(record.id)
        this.$message.success('作废成功')
        this.loadRecords()
      } catch (error) {
        const status = error && error.response && error.response.status
        if (status === 409) {
          this.$message.error('该记录已作废，请勿重复操作')
        } else if (status === 403) {
          this.$message.error('仅记录创建者或管理员可作废')
        } else if (status === 404) {
          this.$message.error('记录不存在')
        } else {
          this.$message.error('作废失败，请稍后重试')
        }
      } finally {
        this.voidingIds = this.voidingIds.filter(id => id !== record.id)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.manual-data-card {
  max-width: 1100px;
}

.manual-data-form {
  margin-top: 8px;
}

.query-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.query-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
</style>
