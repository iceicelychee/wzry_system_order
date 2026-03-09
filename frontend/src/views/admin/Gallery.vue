<template>
  <div class="page-container">
    <el-row :gutter="16">
      <!-- 左侧：图库列表 -->
      <el-col :span="17">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>图库管理</span>
              <el-button type="primary" icon="Upload" @click="showUpload = true">上传图片</el-button>
            </div>
          </template>
          <div class="filter-bar">
            <el-select v-model="filter.category_id" placeholder="全部分类" clearable style="width:140px"
              @change="loadImages">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-input v-model="filter.keyword" placeholder="搜索图片名称/标签" clearable style="width:220px;margin-left:8px"
              prefix-icon="Search" @keyup.enter="loadImages" />
          </div>
          <div class="image-grid" v-loading="loading">
            <div v-for="img in images" :key="img.id" class="image-item">
              <el-image :src="getImageUrl(img.image_url)" fit="cover"
                :preview-src-list="[getImageUrl(img.image_url)]" style="width:100%;height:120px" />
              <div class="image-info">
                <span class="image-name">{{ img.name }}</span>
                <el-popconfirm title="确认删除该图片？" @confirm="handleDelete(img)">
                  <template #reference>
                    <el-button type="danger" link size="small" icon="Delete" />
                  </template>
                </el-popconfirm>
              </div>
            </div>
            <el-empty v-if="images.length === 0 && !loading" description="暂无图片" style="grid-column:1/-1" />
          </div>
          <div class="pagination">
            <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
              :total="pagination.total" layout="total, prev, pager, next" @change="loadImages" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：分类管理 -->
      <el-col :span="7">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>分类管理</span>
              <el-button type="primary" icon="Plus" size="small" @click="showAddCategory = true">新增</el-button>
            </div>
          </template>
          <el-table :data="categories" size="small">
            <el-table-column prop="name" label="分类名称" />
            <el-table-column label="操作" width="60">
              <template #default="{ row }">
                <el-popconfirm title="确认删除该分类？" @confirm="handleDeleteCategory(row)">
                  <template #reference>
                    <el-button type="danger" link size="small" icon="Delete" />
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 上传图片弹窗 -->
    <el-dialog v-model="showUpload" title="上传图片" width="440px">
      <el-form :model="uploadForm" ref="uploadFormRef" label-width="80px">
        <el-form-item label="图片名称" prop="name" :rules="[{required:true,message:'请输入图片名称'}]">
          <el-input v-model="uploadForm.name" placeholder="图片名称" />
        </el-form-item>
        <el-form-item label="所属分类">
          <el-select v-model="uploadForm.category_id" placeholder="选择分类" clearable style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="uploadForm.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
        <el-form-item label="图片文件" prop="image" :rules="[{required:true,message:'请选择图片'}]">
          <el-upload :auto-upload="false" :show-file-list="false" accept=".jpg,.jpeg,.png,.bmp"
            :on-change="handleUploadFile">
            <el-button icon="Upload">选择图片</el-button>
          </el-upload>
          <el-image v-if="uploadPreview" :src="uploadPreview"
            style="width:80px;height:80px;margin-top:8px;border-radius:4px" fit="cover" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 新增分类弹窗 -->
    <el-dialog v-model="showAddCategory" title="新增分类" width="340px">
      <el-input v-model="newCategoryName" placeholder="请输入分类名称" />
      <template #footer>
        <el-button @click="showAddCategory = false">取消</el-button>
        <el-button type="primary" @click="handleAddCategory">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { galleryApi, getImageUrl } from '../../api'

const loading = ref(false)
const images = ref([])
const categories = ref([])
const filter = reactive({ category_id: null, keyword: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

const showUpload = ref(false)
const uploading = ref(false)
const uploadFormRef = ref()
const uploadForm = reactive({ name: '', category_id: null, tags: '', image: null })
const uploadPreview = ref('')

const showAddCategory = ref(false)
const newCategoryName = ref('')

async function loadImages() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filter.category_id) params.category_id = filter.category_id
    if (filter.keyword) params.keyword = filter.keyword
    const res = await galleryApi.list(params)
    images.value = res.list
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  categories.value = await galleryApi.categoryList()
}

function handleUploadFile(file) {
  uploadForm.image = file.raw
  uploadForm.name = uploadForm.name || file.raw.name.replace(/\.[^.]+$/, '')
  uploadPreview.value = URL.createObjectURL(file.raw)
}

async function handleUpload() {
  await uploadFormRef.value.validate()
  if (!uploadForm.image) { ElMessage.error('请选择图片'); return }
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('name', uploadForm.name)
    fd.append('image', uploadForm.image)
    if (uploadForm.category_id) fd.append('category_id', uploadForm.category_id)
    if (uploadForm.tags) fd.append('tags', uploadForm.tags)
    await galleryApi.upload(fd)
    ElMessage.success('上传成功')
    showUpload.value = false
    Object.assign(uploadForm, { name: '', category_id: null, tags: '', image: null })
    uploadPreview.value = ''
    loadImages()
  } finally {
    uploading.value = false
  }
}

async function handleDelete(img) {
  await galleryApi.delete(img.id)
  ElMessage.success('已删除')
  loadImages()
}

async function handleAddCategory() {
  if (!newCategoryName.value.trim()) { ElMessage.error('请输入分类名称'); return }
  await galleryApi.createCategory({ name: newCategoryName.value.trim() })
  ElMessage.success('分类创建成功')
  showAddCategory.value = false
  newCategoryName.value = ''
  loadCategories()
}

async function handleDeleteCategory(cat) {
  await galleryApi.deleteCategory(cat.id)
  ElMessage.success('分类已删除')
  loadCategories()
}

onMounted(() => {
  loadImages()
  loadCategories()
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.filter-bar { display: flex; margin-bottom: 16px; }
.image-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  min-height: 200px;
}
.image-item { border-radius: 6px; overflow: hidden; border: 1px solid #ebeef5; }
.image-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: #fff;
}
.image-name { font-size: 12px; color: #606266; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
