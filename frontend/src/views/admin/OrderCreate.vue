<template>
  <div class="page-container">
    <el-card>
      <template #header><span>创建新订单</span></template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" style="max-width:560px">
        <el-form-item label="订单编号" prop="order_no">
          <el-input v-model="form.order_no" placeholder="留空则自动生成随机编号" clearable />
        </el-form-item>
        <el-form-item label="系统类型" prop="system_type">
          <el-select v-model="form.system_type" placeholder="选择系统类型（可留空由客户填写）" clearable style="width:100%">
            <el-option label="安卓Q区" value="安卓Q区" />
            <el-option label="苹果Q区" value="苹果Q区" />
            <el-option label="安卓V区" value="安卓V区" />
            <el-option label="苹果V区" value="苹果V区" />
          </el-select>
        </el-form-item>
        <el-form-item label="图片" prop="image">
          <div class="upload-area">
            <el-upload ref="uploadRef" :auto-upload="false" :show-file-list="false"
              accept=".jpg,.jpeg,.png,.bmp,.gif,.webp" :on-change="handleLocalFile">
              <el-button icon="Upload">本地上传</el-button>
            </el-upload>
            <el-button icon="Picture" @click="showGallery = true" style="margin-left:8px">图库选图</el-button>
            <div v-if="previewUrl" class="preview-wrap">
              <el-image :src="previewUrl" style="width:80px;height:80px;border-radius:6px;margin-top:8px" fit="cover" />
              <el-button type="danger" link size="small" @click="clearImage" style="display:block;margin-top:4px">移除</el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="备注信息（可选）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">创建订单</el-button>
          <el-button @click="$router.push('/admin/orders')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 创建成功弹窗 -->
    <el-dialog v-model="successDialog" title="订单创建成功" width="460px" :close-on-click-modal="false">
      <div class="success-info">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="订单编号">{{ createdOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="客户链接">
            <el-input v-model="createdOrder.client_link" readonly>
              <template #append>
                <el-button icon="CopyDocument" @click="copyLink(createdOrder.client_link)">复制</el-button>
              </template>
            </el-input>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="successDialog = false; $router.push('/admin/orders')">返回列表</el-button>
        <el-button type="primary" @click="createAnother">继续创建</el-button>
      </template>
    </el-dialog>

    <!-- 图库选图弹窗 -->
    <el-dialog v-model="showGallery" title="图库选图" width="780px">
      <div class="gallery-header">
        <el-select v-model="galleryFilter.category_id" placeholder="全部分类" clearable style="width:140px"
          @change="loadGallery">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-input v-model="galleryFilter.keyword" placeholder="搜索图片名称" clearable style="width:200px;margin-left:8px"
          prefix-icon="Search" @keyup.enter="loadGallery" />
      </div>
      <div class="gallery-grid" v-loading="galleryLoading">
        <div v-for="img in galleryList" :key="img.id" class="gallery-item"
          :class="{ selected: selectedGalleryId === img.id }" @click="selectGalleryImage(img)">
          <el-image :src="getImageUrl(img.image_url)" fit="cover" style="width:100%;height:100%" />
          <div class="gallery-item-name">{{ img.name }}</div>
          <el-icon v-if="selectedGalleryId === img.id" class="check-icon"><Check /></el-icon>
        </div>
        <el-empty v-if="galleryList.length === 0 && !galleryLoading" description="暂无图片" />
      </div>
      <template #footer>
        <el-button @click="showGallery = false">取消</el-button>
        <el-button type="primary" @click="confirmGallery" :disabled="!selectedGalleryId">确认选择</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { orderApi, galleryApi, getImageUrl } from '../../api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const successDialog = ref(false)
const createdOrder = ref({})
const showGallery = ref(false)
const galleryLoading = ref(false)
const galleryList = ref([])
const categories = ref([])
const galleryFilter = reactive({ category_id: null, keyword: '' })
const selectedGalleryId = ref(null)
const selectedGalleryImg = ref(null)

const form = reactive({ order_no: '', system_type: '', remark: '', image: null })
const previewUrl = ref('')
const rules = {}

function handleLocalFile(file) {
  form.image = file.raw
  previewUrl.value = URL.createObjectURL(file.raw)
}

function clearImage() {
  form.image = null
  previewUrl.value = ''
  selectedGalleryId.value = null
  selectedGalleryImg.value = null
}

async function loadGallery() {
  galleryLoading.value = true
  try {
    const params = { page: 1, page_size: 50 }
    if (galleryFilter.category_id) params.category_id = galleryFilter.category_id
    if (galleryFilter.keyword) params.keyword = galleryFilter.keyword
    const res = await galleryApi.list(params)
    galleryList.value = res.list
  } finally {
    galleryLoading.value = false
  }
}

function selectGalleryImage(img) {
  selectedGalleryId.value = img.id
  selectedGalleryImg.value = img
}

async function confirmGallery() {
  if (!selectedGalleryImg.value) return
  // 从图库选择图片，使用图库图片URL
  const img = selectedGalleryImg.value
  previewUrl.value = getImageUrl(img.image_url)
  // 将图库图片转为File对象
  try {
    const res = await fetch(getImageUrl(img.image_url))
    const blob = await res.blob()
    form.image = new File([blob], img.name + '.jpg', { type: blob.type })
  } catch {
    ElMessage.warning('图片加载失败，请尝试本地上传')
  }
  showGallery.value = false
}

async function handleSubmit() {
  loading.value = true
  try {
    const formData = new FormData()
    if (form.order_no) formData.append('order_no', form.order_no)
    if (form.system_type) formData.append('system_type', form.system_type)
    if (form.remark) formData.append('remark', form.remark)
    if (form.image) formData.append('image', form.image)
    const res = await orderApi.create(formData)
    createdOrder.value = res.order
    successDialog.value = true
  } finally {
    loading.value = false
  }
}

function copyLink(link) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(link).then(() => ElMessage.success('链接已复制'))
  } else {
    const el = document.createElement('textarea')
    el.value = link
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    ElMessage.success('链接已复制')
  }
}

function createAnother() {
  successDialog.value = false
  Object.assign(form, { order_no: '', system_type: '', remark: '', image: null })
  previewUrl.value = ''
}

onMounted(async () => {
  const res = await galleryApi.categoryList()
  categories.value = res
  loadGallery()
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.upload-area { display: flex; flex-wrap: wrap; align-items: center; }
.preview-wrap { width: 100%; }
.success-info { padding: 8px 0; }
.gallery-header { display: flex; margin-bottom: 16px; }
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}
.gallery-item {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}
.gallery-item:hover { border-color: #409eff; }
.gallery-item.selected { border-color: #409eff; }
.gallery-item-name {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 11px;
  padding: 3px 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.check-icon {
  position: absolute;
  top: 6px; right: 6px;
  color: #fff;
  background: #409eff;
  border-radius: 50%;
  padding: 2px;
  font-size: 14px;
}
</style>
